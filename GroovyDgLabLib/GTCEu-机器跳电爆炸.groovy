// GT 机器跳电 -> 电人（游戏内电击伤害）+ DG-LAB 联动
// 接口对照源码：C:\Users\FengMang\Desktop\Minecraft源码\GregTech-2.8.10
// 依赖：dglab_main.groovy 已加载，且执行过 /dglab-login-v3
//
// GroovyScript 1.4.3 事件机制（已反编译确认 GroovyEventManager）：
//   监听闭包是「空参数调用」的，真正的 event 被 setDelegate(event)。
//   所以闭包参数永远是 null，必须用 delegate 取事件对象！
//
// 触发：缺电停摆(isHasNotEnoughEnergy) / 过压爆炸(ExplosionEvent)

import java.util.concurrent.ConcurrentHashMap
import net.minecraft.entity.player.EntityPlayer
import net.minecraft.tileentity.TileEntity
import net.minecraft.util.math.AxisAlignedBB
import gregtech.api.metatileentity.interfaces.IGregTechTileEntity
import gregtech.api.metatileentity.multiblock.IMaintenance
import gregtech.api.metatileentity.multiblock.RecipeMapMultiblockController
import gregtech.api.damagesources.DamageSources

// ================= 可调参数 =================
final double  SHOCK_RADIUS   = 6.0d
final float   SHOCK_DAMAGE   = 3.0f
final long    COOLDOWN_MS    = 1200L
final String  DGLAB_CHANNEL  = 'A'
final int     PULSE_HZ       = 80
// ---- 渐强波形参数（跳电后持续输出，强度随时间从 START 升到 MAX 后保持）----
final int     WAVE_START     = 5     // 起始强度 0~100
final int     WAVE_MAX       = 80    // 最高强度 0~100
final long    WAVE_DURATION  = 8000L // 从 START 渐强到 MAX 用时(ms)，之后保持 MAX
// ===========================================

final String SHOCK_MARK   = 'gt.shock.mark'
final String SHOCK_BAD    = 'gt.shock.bad'          // 服务端实时写：当前是否有机器处于故障/缺电
final String WAVE_RUNNING = 'gt.shock.wave.running'
final String WAVE_BEGIN   = 'gt.shock.wave.begin'
final String WAVE_STOP    = 'gt.shock.wave.stop'    // true=请求波形线程停止
final String WAVE_EPOCH   = 'gt.shock.wave.epoch'   // 重载代数，旧线程检测后自行退出
Map<String, Boolean> prevBad = new ConcurrentHashMap<>()
java.util.concurrent.atomic.AtomicBoolean anyBad = new java.util.concurrent.atomic.AtomicBoolean(false)
long lastServerMark = 0L
long lastFullSweep  = 0L
long clientLast     = 0L

def markShock = {
    String ts = System.currentTimeMillis().toString()
    System.getProperties().put(SHOCK_MARK, ts)
    log.info('[GT跳电] 打标记 mark=' + ts)
}

// 取世界里的 TileEntity 列表：Cleanroom 改了方法映射，多来源兜底
// 关键：遍历所有父类所有 Collection 字段，选「元素确实是 TileEntity」的非空集合
def getTiles = { def world ->
    def best = null
    def cls = world.getClass()
    while (cls != null) {
        for (def f : cls.getDeclaredFields()) {
            try {
                if (!java.util.Collection.isAssignableFrom(f.getType())) continue
                f.setAccessible(true)
                def r = f.get(world)
                if (!(r instanceof java.util.Collection) || r.isEmpty()) continue
                def first = r.iterator().next()
                if (first == null || !(first instanceof net.minecraft.tileentity.TileEntity)) continue
                best = r
                break
            } catch (Throwable ignored) {}
        }
        if (best != null) break
        cls = cls.getSuperclass()
    }
    if (best == null) {
        // 退而求其次：任何非空的 Collection 字段
        cls = world.getClass()
        while (cls != null && best == null) {
            for (def f : cls.getDeclaredFields()) {
                try {
                    if (!java.util.Collection.isAssignableFrom(f.getType())) continue
                    f.setAccessible(true)
                    def r = f.get(world)
                    if (r instanceof java.util.Collection && !r.isEmpty()) { best = r; break }
                } catch (Throwable ignored) {}
            }
            cls = cls.getSuperclass()
        }
    }
    return best ?: []
}

// ---------- 扫描指定世界（服务端世界为准） ----------
// 返回该世界缺电机器数量；同时执行电击
def scanWorld = { def world ->
    if (world == null) return 0
    long now = System.currentTimeMillis()
    boolean cooling = (now - lastServerMark < COOLDOWN_MS)

    int badCount = 0
    def tiles = getTiles(world)
    for (Object te : tiles) {
        if (!(te instanceof IGregTechTileEntity) || !(te instanceof TileEntity)) continue
        def mte = ((IGregTechTileEntity) te).getMetaTileEntity()
        if (mte == null) continue

        // 只认「运行中且缺电停摆」：必须 workingEnabled && isActive && isHasNotEnoughEnergy。
        // 原因：机器关闭(workingEnabled=false)时 hasNotEnoughEnergy 不会清，会卡 true -> 会导致关了还输出。
        // 维护故障(trb)不算、不电击、不触发波形。
        boolean lowPower = false
        if (mte instanceof RecipeMapMultiblockController) {
            try {
                def wk = ((RecipeMapMultiblockController) mte).getRecipeMapWorkable()
                // 不用 isActive()：缺电瞬间它会波动。只用 workingEnabled + hasNotEnoughEnergy。
                if (wk != null && wk.isWorkingEnabled() && wk.isHasNotEnoughEnergy()) {
                    lowPower = true
                }
            } catch (Throwable ignored) {}
        }
        if (lowPower) badCount++

        def pos = ((TileEntity) te).getPos()
        String key = world.provider.getDimension() + ':' + pos.getX() + ',' + pos.getY() + ',' + pos.getZ()
        boolean was = prevBad.containsKey(key) ? prevBad.get(key) : false
        boolean seen = prevBad.containsKey(key)   // 第一次见到这台机器：只登记，不触发
        prevBad.put(key, lowPower)

        // 边沿触发：只有「已登记过 && 从正常变为缺电」才电一下；新放的机器不触发
        boolean newlyBroken = seen && lowPower && !was
        if (cooling || !newlyBroken) continue
        def box = new AxisAlignedBB(pos).grow(SHOCK_RADIUS)
        def victims = []
        try { victims = world.getEntitiesWithinAABB(EntityPlayer, box) } catch (Throwable ignored) {}
        if (!victims) {
            try {
                for (Object p : world.playerEntities) {
                    try {
                        if (p instanceof EntityPlayer && p.getDistanceSq(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5) <= SHOCK_RADIUS * SHOCK_RADIUS) victims.add(p)
                    } catch (Throwable ignored) {}
                }
            } catch (Throwable ignored) {}
        }
        for (Object o : victims) {
            if (!(o instanceof EntityPlayer)) continue
            EntityPlayer p = (EntityPlayer) o
            p.attackEntityFrom(DamageSources.getElectricDamage(), SHOCK_DAMAGE)
            log.info('[GT跳电] 电击玩家 ' + p.getName() + ' 伤害=' + SHOCK_DAMAGE + ' 位置=' + pos.getX() + ',' + pos.getY() + ',' + pos.getZ())
        }
        if (victims.isEmpty()) log.info('[GT跳电] 半径 ' + SHOCK_RADIUS + ' 内没有玩家，未造成电击')
        lastServerMark = now
        log.info('[GT跳电] 缺电 ' + key)
        break
    }
    return badCount
}

// ---------- WorldTickEvent：用 delegate 取事件，拿服务端世界 ----------
event_manager.listen(net.minecraftforge.fml.common.gameevent.TickEvent.WorldTickEvent) { param ->
    try {
        // WorldTickEvent 每个世界都触发，但 ev.world 可能是末地/下界。
        // 遍历所有维度的服务端世界，保证主世界的机器被扫到（GT 控制器通常在主世界）。
        // 每 50ms 只做一次全维度扫描（因为本事件每个世界都会触发一次，避免重复扫 N 遍）
        long wall = System.currentTimeMillis()
        if (wall - lastFullSweep < 50L) return
        lastFullSweep = wall
        int totalBad = 0
        for (int dim = -1; dim <= 15; dim++) {
            def dw = null
            try { dw = net.minecraftforge.common.DimensionManager.getWorld(dim) } catch (Throwable ignored) {}
            if (dw == null || dw.isRemote) continue
            totalBad += scanWorld(dw) as int
        }
        // 把「当前是否有机器缺电」实时写到 System 属性，供波形线程决定启停
        boolean badNow = totalBad > 0
        System.getProperties().put(SHOCK_BAD, badNow ? 'true' : 'false')
        if (badNow != anyBad.get()) {
            anyBad.set(badNow)
            log.info('[GT跳电] 缺电状态变化 -> ' + (badNow ? '有机器缺电(开波形)' : '全部恢复(停波形)'))
        }
    } catch (Throwable e) {
        log.info('[GT跳电] WorldTick扫描异常: ' + e)
        // 异常时按「无缺电」处理，避免波形卡在一直输出
        System.getProperties().put(SHOCK_BAD, 'false')
        anyBad.set(false)
    }
}

// ---------- 构造波形帧 ----------
// 实测(抓包 dglab_capture.log)：帧第1字节是「间隙」、第5字节是「导通/脉宽」。
// 间隙越大越弱、导通越大越强。要从低到高：第1字节=间隙(100-s)递减、第5字节=导通(s)递增。
// 与 dglab_main.groovy 修复后的 smoothPulse() 完全同构。
final int WAVE_PERIOD = 100   // 一个周期的总量
def makeWaveFrame = { int strength ->
    int s = Math.min(100, Math.max(1, strength))       // s = 导通强度，随时间递增
    int gap = Math.max(1, WAVE_PERIOD - s)             // 间隙随时间递减
    // [间隙,0,0,0, 导通,0,0,0]
    return String.format('%02X%02X%02X%02X%02X%02X%02X%02X', gap, 0, 0, 0, s, 0, 0, 0)
}

// ---------- 渐强波形后台线程 ----------
// 直接调底层 srv.sendMsg() 下发 pulse：V3 的 d.pulse() 内部 sleep(帧数*100ms) 会卡主线程，
// 所以绕过它，后台线程自己控制节奏；WebSocket 发送本身线程安全(sendJson 内有 synchronized)。
def startWaveThread = {
    Object running = System.getProperties().get(WAVE_RUNNING)
    if (running?.toString() == 'true') return  // 已在跑，不重复开
    System.getProperties().put(WAVE_RUNNING, 'true')
    System.getProperties().put(WAVE_STOP, 'false')
    final long myEpoch = (System.getProperties().get(WAVE_EPOCH) ?: '0') as long
    Thread t = new Thread({
        log.info('[GT跳电][波形] 线程启动 epoch=' + myEpoch)
        def srv = null
        try {
            def ctrl = System.getProperties().get('dglab.ctrl.instance')
            if (ctrl != null) srv = ctrl.srv
        } catch (Throwable ignored) {}
        try {
            long begin = System.currentTimeMillis()
            System.getProperties().put(WAVE_BEGIN, begin.toString())
            while (true) {
                if (System.getProperties().get(WAVE_STOP)?.toString() == 'true') break
                if (((System.getProperties().get(WAVE_EPOCH) ?: '0') as long) != myEpoch) {
                    log.info('[GT跳电][波形] epoch 变化，旧线程退出')
                    break
                }
                // 机器恢复（没有机器缺电）-> 立刻停波形
                if (System.getProperties().get(SHOCK_BAD)?.toString() != 'true') {
                    log.info('[GT跳电][波形] 机器已恢复/关闭，停波形')
                    break
                }
                long now = System.currentTimeMillis()
                // 强度按已运行时间渐强，到顶后保持 MAX
                double ratio = Math.min(1.0d, (double)(now - begin) / (double) WAVE_DURATION)
                int strength = (int) Math.round(WAVE_START + (WAVE_MAX - WAVE_START) * ratio)
                List<String> frames = (1..5).collect { makeWaveFrame(strength) }
                String json = '["' + frames.join('","') + '"]'
                try {
                    if (srv != null) {
                        srv.sendMsg('pulse-' + DGLAB_CHANNEL + ':' + json)
                    } else {
                        log.info('[GT跳电][波形] 无可用控制器(DG-LAB V3 未启动?)，停止')
                        break
                    }
                    log.info('[GT跳电][波形] 下发 strength=' + strength + ' 帧=' + frames[0])
                } catch (Throwable pe) {
                    log.info('[GT跳电][波形] pulse下发异常: ' + pe)
                }
                Thread.sleep(500L)
            }
        } catch (Throwable e) {
            log.info('[GT跳电][波形] 线程异常: ' + e)
        } finally {
            try {
                def dd = new DgLab()
                dd.clearPulse(DGLAB_CHANNEL)
                log.info('[GT跳电][波形] 已 clearPulse')
            } catch (Throwable ignored) {}
            System.getProperties().put(WAVE_RUNNING, 'false')
            log.info('[GT跳电][波形] 线程结束')
        }
    } as Runnable, 'GT-Shock-Wave-' + myEpoch)
    t.setDaemon(true)
    t.start()
}

// ---------- 客户端 ClientTickEvent：根据 SHOCK_BAD 启停波形 ----------
// 单人/集成服：服务端与客户端共享 JVM 的 System 属性，SHOCK_BAD 由服务端扫描实时写入。
event_manager.listen(net.minecraftforge.fml.common.gameevent.TickEvent.ClientTickEvent) { param ->
    try {
        boolean bad = System.getProperties().get(SHOCK_BAD)?.toString() == 'true'
        boolean running = System.getProperties().get(WAVE_RUNNING)?.toString() == 'true'
        if (bad && !running) {
            // 有机器缺电且波形没在跑 -> 启动（需已连接设备）
            def d0 = new DgLab()
            if (d0.connected) {
                log.info('[GT跳电] 检测到缺电机器，启动渐强波形')
                startWaveThread()
            } else {
                log.info('[GT跳电] 有缺电机器但 DG-LAB 未连接，请先 /dglab-login-v3')
            }
        }
        // 停止由波形线程自己检测 SHOCK_BAD=false 完成（见线程内 break）
    } catch (Throwable e) {
        log.info('[GT跳电] DG-LAB 波形驱动失败: ' + e)
    }
}

// ---------- 过压爆炸 -> 电击（event 用 delegate 取） ----------
try {
    event_manager.listen(Class.forName('net.minecraftforge.event.world.ExplosionEvent$Start')) { param ->
        try {
            Object ev = param
            if (ev == null) { try { ev = delegate } catch (Throwable ignored) {} }
            if (ev == null) return
            def w = ev.getWorld()
            if (w == null || w.isRemote) return
            def ex = ev.explosion.explosionX, ey = ev.explosion.explosionY, ez = ev.explosion.explosionZ
            def pos = new net.minecraft.util.math.BlockPos(ex as int, ey as int, ez as int)
            def box = new AxisAlignedBB(pos).grow(SHOCK_RADIUS)
            def victims2 = []
            try { victims2 = w.getEntitiesWithinAABB(EntityPlayer, box) } catch (Throwable ignored) {}
            for (Object o : victims2) {
                if (!(o instanceof EntityPlayer)) continue
                EntityPlayer p = (EntityPlayer) o
                p.attackEntityFrom(DamageSources.getElectricDamage(), SHOCK_DAMAGE)
                log.info('[GT跳电] 爆炸电击玩家 ' + p.getName() + ' 伤害=' + SHOCK_DAMAGE)
            }
            markShock()
            log.info('[GT跳电] 爆炸 ' + pos.getX() + ',' + pos.getY() + ',' + pos.getZ() + ' 命中玩家数=' + victims2.size())
        } catch (Throwable e) {
            log.info('[GT跳电] 爆炸电击失败: ' + e)
        }
    }
} catch (Throwable e) { log.info('[GT跳电] 爆炸事件注册失败: ' + e) }

// ---------- 电击音效 -> DG-LAB（event 用 delegate 取） ----------
try {
    event_manager.listen(Class.forName('net.minecraftforge.client.event.sound.PlaySoundEvent')) { param ->
        try {
            Object ev = param
            if (ev == null) { try { ev = delegate } catch (Throwable ignored) {} }
            if (ev == null) return
            String n = (ev.getName() ?: '').toString().toLowerCase()
            if (!n) { def s = ev.getSound(); if (s != null) n = (s.getSoundLocation() ?: '').toString().toLowerCase() }
            if (n.contains('maintenance.electrical') || n.contains('electrical')) {
                log.info('[GT跳电] 捕获电击音效 sound=' + n)
                markShock()
            }
        } catch (Throwable ignored) {}
    }
} catch (Throwable ignored) {}

// 热重载：epoch+1 让旧波形线程自行退出；清 running 标志；
// 关键：把 clientLast 设为「当前标记」，避免重载瞬间读到旧标记误触发一次波形。
Object curMark = System.getProperties().get(SHOCK_MARK)
if (curMark != null) { try { clientLast = Long.parseLong(curMark.toString()) } catch (Throwable ignored) {} }
long newEpoch = (((System.getProperties().get(WAVE_EPOCH) ?: '0') as long) + 1L)
System.getProperties().put(WAVE_EPOCH, newEpoch.toString())
System.getProperties().put(WAVE_RUNNING, 'false')
System.getProperties().put(WAVE_STOP, 'true')
System.getProperties().put(SHOCK_BAD, 'false')
anyBad.set(false)

// 停止波形的客户端命令
try {
    mods.minecraft.command.registerClientCommand('gtwavestop', '/gtwavestop - 停止GT跳电波形') { s, sender, args ->
        System.getProperties().put(WAVE_STOP, 'true')
        log.info('[GT跳电][波形] 收到停止命令')
    }
} catch (Throwable ignored) {}

log.info('[GT跳电] 已加载：缺电跳电 -> 渐强波形；/gtwavestop 停止')

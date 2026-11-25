// gt_cable_shock.groovy — 踩到「无包皮(裸)电缆」触电 -> DG-LAB 波形，强度按电缆电流
// 接口对照源码：GregTech-2.8.10 BlockCable.onEntityCollision / TileEntityCable
// 依赖：dglab_main.groovy（V3）已加载并 /dglab-login-v3
//
// GT 原生判定(BlockCable.java:164)：裸线 insulationLevel==-1、无 frame、loss>0、voltage>0、amperage>0
// 本脚本不重复扣血（GT 已用电击伤害扣），只按电流驱动 DG-LAB 波形。
// 波形帧格式与 dglab_main.smoothPulse 修复版一致：[间隙,0,0,0, 强度,0,0,0]

import java.util.concurrent.ConcurrentHashMap
import net.minecraftforge.fml.common.gameevent.TickEvent
import net.minecraft.entity.player.EntityPlayer
import net.minecraft.tileentity.TileEntity
import net.minecraft.util.math.BlockPos
import gregtech.common.pipelike.cable.tile.TileEntityCable
import gregtech.api.damagesources.DamageSources

// ================= 可调参数 =================
final double  CHECK_Y      = 1.6d     // 脚部上下判定范围（格）
final long    REARM_MS     = 600L     // 同一玩家再次触发的最小间隔
final long    GRACE_MS     = 1200L    // 离开电缆后波形再持续的时间(ms)
final int     WAVE_MIN     = 5        // 最小强度(0~100)
final int     WAVE_MAX     = 100      // 最大强度
final double  AMP_FULL     = 32.0d    // 电流达到该值时强度=WAVE_MAX（按你的线材电流调）
final String  DGLAB_CHANNEL = 'A'
// ===========================================

final String P_MARK    = 'gt.cable.shock.mark'     // 触发时间戳
final String P_UNTIL   = 'gt.cable.wave.until'     // 波形持续到
final String P_STRENGTH= 'gt.cable.wave.strength'  // 当前目标强度(由电流算出)
final String P_RUNNING = 'gt.cable.wave.running'
final String P_STOP    = 'gt.cable.wave.stop'
final String P_EPOCH   = 'gt.cable.wave.epoch'
final String P_DIAG    = 'gt.cable.diag'

Map<String, Long> lastFire = new ConcurrentHashMap<>()
long lastSweep = 0L

// 反射取 tile（Cleanroom 改映射，多名字兜底）
def getTE = { def w, BlockPos bp ->
    for (String m : ['getTileEntity', 'func_175625_s']) {
        try { return w.getClass().getMethod(m, BlockPos).invoke(w, bp) } catch (Throwable ignored) {}
    }
    return null
}

def markWave = { double amp ->
    int s = (int) Math.round(WAVE_MIN + (WAVE_MAX - WAVE_MIN) * Math.min(1.0d, amp / AMP_FULL))
    s = Math.max(WAVE_MIN, Math.min(WAVE_MAX, s))
    System.getProperties().put(P_STRENGTH, s.toString())
    System.getProperties().put(P_UNTIL, (System.currentTimeMillis() + GRACE_MS).toString())
    System.getProperties().put(P_MARK, System.currentTimeMillis().toString())
    return s
}

// ---------- 服务端：找玩家脚下的裸电缆 ----------
event_manager.listen(net.minecraftforge.fml.common.gameevent.TickEvent.WorldTickEvent) { param ->
    try {
        long wall = System.currentTimeMillis()
        if (wall - lastSweep < 100L) return   // 每 100ms 查一次
        lastSweep = wall
        StringBuilder dbg = new StringBuilder()
        for (int dim = -1; dim <= 15; dim++) {
            def w = null
            try { w = net.minecraftforge.common.DimensionManager.getWorld(dim) } catch (Throwable ignored) {}
            if (w == null || w.isRemote) continue
            for (Object po : w.playerEntities) {
                if (!(po instanceof EntityPlayer)) continue
                EntityPlayer p = (EntityPlayer) po
                BlockPos feet
                try { feet = p.getPosition() } catch (Throwable ignored) { continue }
                // 检查脚所在格和下一格
                for (int dy = 0; dy <= 1; dy++) {
                    BlockPos bp = feet.down(dy)
                    def te = getTE(w, bp)
                    if (!(te instanceof TileEntityCable)) continue
                    TileEntityCable cable = (TileEntityCable) te
                    try {
                        def ins = cable.getPipeType()
                        if (ins == null || ins.insulationLevel != -1) continue  // 有包皮不算
                        if (cable.getFrameMaterial() != null) continue
                        if (cable.getNodeData().getLossPerBlock() <= 0) continue
                        long volt = cable.getCurrentMaxVoltage()
                        double amp = cable.getAverageAmperage()
                        if (volt <= 0 || amp <= 0) continue
                        // 高度范围：玩家确实贴着这根线
                        double dx = p.posX - (bp.getX() + 0.5)
                        double dz = p.posZ - (bp.getZ() + 0.5)
                        double dy2 = p.posY - bp.getY()
                        if (dx*dx + dz*dz > 1.2d || dy2 < -0.5d || dy2 > CHECK_Y) continue

                        String key = p.getName()
                        long lastT = lastFire.getOrDefault(key, 0L)
                        if (wall - lastT < REARM_MS) continue
                        lastFire.put(key, wall)
                        int strength = markWave(amp)
                        log.info('[裸线触电] ' + key + ' 电流=' + String.format('%.1f', amp) +
                                 ' 电压=' + volt + ' 波形强度=' + strength + ' @' + bp.getX()+','+bp.getY()+','+bp.getZ())
                        dbg.append(key).append(' amp=').append(String.format('%.1f', amp)).append(' s=').append(strength).append(' ')
                    } catch (Throwable e) {
                        log.info('[裸线触电] 检测异常: ' + e)
                    }
                }
            }
        }
        if (dbg.length() > 0) System.getProperties().put(P_DIAG, dbg.toString())
    } catch (Throwable e) {
        log.info('[裸线触电] 扫描异常: ' + e)
    }
}

// ---------- 波形帧 ----------
final int WAVE_PERIOD = 100
def makeFrame = { int s ->
    int v = Math.max(WAVE_MIN, Math.min(WAVE_MAX, s))
    int gap = Math.max(1, WAVE_PERIOD - v)
    return String.format('%02X%02X%02X%02X%02X%02X%02X%02X', gap, 0, 0, 0, v, 0, 0, 0)
}

// ---------- 波形线程：持续到 GRACE 超时，强度取电流映射值 ----------
def startWave = {
    if (System.getProperties().get(P_RUNNING)?.toString() == 'true') return
    System.getProperties().put(P_RUNNING, 'true')
    System.getProperties().put(P_STOP, 'false')
    final long epoch = (System.getProperties().get(P_EPOCH) ?: '0') as long
    Thread t = new Thread({
        log.info('[裸线触电][波形] 线程启动')
        def srv = null
        try { def c = System.getProperties().get('dglab.ctrl.instance'); if (c != null) srv = c.srv } catch (Throwable ignored) {}
        try {
            while (true) {
                if (System.getProperties().get(P_STOP)?.toString() == 'true') break
                if (((System.getProperties().get(P_EPOCH) ?: '0') as long) != epoch) break
                long until = (System.getProperties().get(P_UNTIL) ?: '0') as long
                if (System.currentTimeMillis() > until) break
                int s = (System.getProperties().get(P_STRENGTH) ?: '5') as int
                List<String> frames = (1..5).collect { makeFrame(s) }
                String json = '["' + frames.join('","') + '"]'
                if (srv != null) {
                    srv.sendMsg('pulse-' + DGLAB_CHANNEL + ':' + json)
                    log.info('[裸线触电][波形] 输出 strength=' + s)
                } else { log.info('[裸线触电][波形] DG-LAB 未连接，停止'); break }
                Thread.sleep(500L)
            }
        } catch (Throwable e) {
            log.info('[裸线触电][波形] 异常: ' + e)
        } finally {
            try { def d = new DgLab(); d.clearPulse(DGLAB_CHANNEL) } catch (Throwable ignored) {}
            System.getProperties().put(P_RUNNING, 'false')
            log.info('[裸线触电][波形] 线程结束')
        }
    } as Runnable, 'GT-Cable-Shock-Wave')
    t.setDaemon(true)
    t.start()
}

// ---------- 客户端：有标记就起波形 ----------
event_manager.listen(net.minecraftforge.fml.common.gameevent.TickEvent.ClientTickEvent) { param ->
    try {
        Object mark = System.getProperties().get(P_MARK)
        if (mark == null) return
        long until = (System.getProperties().get(P_UNTIL) ?: '0') as long
        if (System.currentTimeMillis() > until) return
        if (System.getProperties().get(P_RUNNING)?.toString() == 'true') return
        def d = new DgLab()
        if (d.connected) startWave()
    } catch (Throwable e) {
        log.info('[裸线触电] 波形触发失败: ' + e)
    }
}

// 重载重置
long ep = (((System.getProperties().get(P_EPOCH) ?: '0') as long) + 1L)
System.getProperties().put(P_EPOCH, ep.toString())
System.getProperties().put(P_RUNNING, 'false')
System.getProperties().put(P_STOP, 'true')
log.info('[裸线触电] 已加载：踩裸电缆 -> 波形强度随电流；/dglab-login-v3 后生效')

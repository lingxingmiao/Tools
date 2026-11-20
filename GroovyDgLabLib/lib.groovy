// side: client

// dglab_ws.groovy — 【纯 GrS 一体方案】GroovyScript 内置 DG-LAB V3 WebSocket 服务端
// 放置到：minecraft/groovy/postInit/dglab_ws.groovy
// 不需要 Minecraft-DG-LAB 模组、不需要 KubeJS、不需要外部中转服务器或 Python！
// GrS 自己开 ServerSocket，DG-LAB App 扫码直连本机，脚本直接下发强度/波形。
// 依赖：仅 JDK（java.net.Socket/ServerSocket + SHA1/Base64）+ Groovy 自带能力；破解版 GrS 需允许线程/网络
// 协议：https://github.com/LemoBits/DGLAB-docs/blob/37f66a8.../docs/socket-control.md
//
// ==================== 对外接口（其它脚本这样调用） ====================
// 本脚本把控制器实例存进 JVM 级 System Properties，任何脚本都能取到：
//   def ctrl = System.getProperties().get('dglab.ctrl.instance')
//   def srv  = System.getProperties().get('dglab.server.instance')
//
// DGLabCtrl 控制 API（ch = 'A' 或 'B'）：
//   ctrl.bound                      是否有 App 已绑定（getter isBound）
//   ctrl.addStrength(ch, v)         增加强度 v（0~200）
//   ctrl.reduceStrength(ch, v)      减少强度 v
//   ctrl.setStrength(ch, v)         设定强度到 v（0~200）
//   ctrl.clearPulse(ch)             清空该通道波形队列（紧急停止）
//   ctrl.pulse(ch, hexFrames)       下发波形帧 List<String>，每帧8字节HEX、每帧100ms
//   DGLabCtrl.smoothPulse(freq, strength, frames)  生成固定频率/强度的波形帧
//     freq: 10~1000Hz, strength: 0~100, frames: 帧数(×100ms=时长)
//
// 底层（DGLabLocalServer）：
//   srv.sendMsg(String)             直接发原始 V3 业务消息（如 'strength-1+1+5'）
//   srv.getQrCode(lanIp)            获取扫码链接
//   srv.apps                        已绑定的 App 映射（clientId -> WsConn）
//
// 示例：其它脚本里受伤时加强度并给一段波形
//   def ctrl = System.getProperties().get('dglab.ctrl.instance')
//   if (ctrl?.bound) {
//       ctrl.addStrength('A', 10)
//       ctrl.pulse('A', DGLabCtrl.smoothPulse(50, 30, 10))
//   }
// =================================================================

import java.net.Socket
import java.net.ServerSocket
import java.io.*
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import java.util.concurrent.ConcurrentHashMap

// ---------- JSON 工具：优先 groovy.json，缺失回退到自带 MinimalJson ----------
class MinimalJson {
    static String toJson(Object o) {
        if (o == null) return 'null'
        if (o instanceof CharSequence) {
            String s = o.toString().replace('\\', '\\\\').replace('"', '\\"')
                    .replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            return '"' + s + '"'
        }
        if (o instanceof Number || o instanceof Boolean) return o.toString()
        if (o instanceof Map) return '{' + o.collect { k, v -> toJson(k.toString()) + ':' + toJson(v) }.join(',') + '}'
        if (o instanceof Iterable) return '[' + o.collect { toJson(it) }.join(',') + ']'
        if (o.getClass().isArray()) return '[' + o.collect { toJson(it) }.join(',') + ']'
        return '"' + o.toString() + '"'
    }
    static Object parseText(String s) { new P(s).value() }
    private static class P {
        final String s; int i = 0
        P(String s) { this.s = s }
        Object value() {
            ws(); char c = s.charAt(i)
            if (c == '{') return obj()
            if (c == '[') return arr()
            if (c == '"') return str()
            if (c == 't') { i += 4; return true }
            if (c == 'f') { i += 5; return false }
            if (c == 'n') { i += 4; return null }
            return num()
        }
        Map obj() {
            Map m = [:]; i++; ws()
            while (s.charAt(i) != '}') {
                String k = str(); ws(); i++; ws()
                m[k] = value(); ws()
                if (s.charAt(i) == ',') { i++; ws() } else break
            }
            i++; return m
        }
        List arr() {
            List a = []; i++; ws()
            while (s.charAt(i) != ']') {
                a << value(); ws()
                if (s.charAt(i) == ',') { i++; ws() } else break
            }
            i++; return a
        }
        String str() {
            StringBuilder b = new StringBuilder(); i++
            while (i < s.length()) {
                char c = s.charAt(i++)
                if (c == '"') break
                if (c == '\\' && i < s.length()) {
                    char d = s.charAt(i++)
                    b << (d == 'n' ? '\n' : d == 'r' ? '\r' : d == 't' ? '\t' : d)
                } else b << c
            }
            return b.toString()
        }
        Object num() {
            int st = i
            while (i < s.length() && ((String)s.charAt(i)).matches('[-+0-9.eE]')) i++
            String n = s.substring(st, i)
            return (n.contains('.') || n.contains('e') || n.contains('E')) ? (double)Double.parseDouble(n) : (int)Integer.parseInt(n)
        }
        void ws() { while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++ }
    }
}
class Json {
    static Class SLURPER, OUTPUT
    static {
        try { SLURPER = Class.forName('groovy.json.JsonSlurper') } catch (Throwable ignored) {}
        try { OUTPUT  = Class.forName('groovy.json.JsonOutput')  } catch (Throwable ignored) {}
    }
    static String out(Object o) {
        if (OUTPUT != null) { try { return OUTPUT.newInstance().toJson(o) as String } catch (Throwable ignored) {} }
        return MinimalJson.toJson(o)
    }
    static Object parse(String s) {
        if (SLURPER != null) { try { return SLURPER.newInstance().parseText(s) } catch (Throwable ignored) {} }
        return MinimalJson.parseText(s)
    }
}

// ---------- 单条 WebSocket 连接（服务端侧：发送不加 mask，接收解 mask） ----------
class WsConn {
    final Socket sock
    final OutputStream out
    final InputStream inp
    volatile boolean open = true

    WsConn(Socket s) { sock = s; out = s.getOutputStream(); inp = s.getInputStream() }

    /** 读 HTTP 握手头，返回请求 path（如 /<终端ID>） */
    String handshake() {
        ByteArrayOutputStream hb = new ByteArrayOutputStream()
        int c
        while ((c = inp.read()) != -1) {
            hb.write(c)
            byte[] a = hb.toByteArray()
            if (a.length >= 4 && a[a.length-4] == 13 && a[a.length-3] == 10 && a[a.length-2] == 13 && a[a.length-1] == 10) break
        }
        String hdr = hb.toString('ISO-8859-1')
        List<String> lines = hdr.readLines()
        String req = lines.isEmpty() ? '' : lines[0]
        String path = req.split(' ').length > 1 ? req.split(' ')[1] : '/'
        String key = lines.find { it.toLowerCase().startsWith('sec-websocket-key') }?.split(':')?.getAt(1)?.trim()
        if (!key) throw new IOException('缺少 Sec-WebSocket-Key: ' + hdr.take(120))
        String accept = Base64.encoder.encodeToString(
                MessageDigest.getInstance('SHA-1').digest((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').getBytes('ASCII')))
        String resp = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ${accept}\r\n\r\n"
        out.write(resp.getBytes('ASCII')); out.flush()
        return path
    }

    void sendText(String text) {
        byte[] data = text.getBytes(StandardCharsets.UTF_8)
        ByteArrayOutputStream f = new ByteArrayOutputStream()
        f.write(0x81)
        int n = data.length
        if (n < 126) f.write(n)
        else if (n <= 65535) { f.write(126); f.write((n >>> 8) & 0xFF); f.write(n & 0xFF) }
        else { f.write(127); for (int i = 7; i >= 0; i--) f.write((n >>> (i * 8)) & 0xFF) }
        f.write(data)
        synchronized (out) { out.write(f.toByteArray()); out.flush() }
    }
    void sendJson(Map m) { sendText(Json.out(m)) }

    /** 阻塞读一条文本帧；ping 自动回 pong；关闭返回 null */
    String readText() {
        while (true) {
            int b1 = inp.read(); if (b1 < 0) { open = false; return null }
            int opcode = b1 & 0x0F
            int b2 = inp.read(); if (b2 < 0) { open = false; return null }
            boolean masked = (b2 & 0x80) != 0
            long len = b2 & 0x7F
            if (len == 126) len = ((inp.read() & 0xFF) << 8) | (inp.read() & 0xFF)
            else if (len == 127) { len = 0; for (int i = 0; i < 8; i++) len = (len << 8) | (inp.read() & 0xFF) }
            byte[] mask = null
            if (masked) { mask = new byte[4]; for (int i = 0; i < 4; i++) mask[i] = (byte) inp.read() }
            int total = (int) len
            byte[] data = new byte[total]; int off = 0
            while (off < total) {
                int r = inp.read(data, off, total - off)
                if (r < 0) break
                off += r
            }
            if (masked) for (int i = 0; i < total; i++) data[i] = (byte)(data[i] ^ mask[i % 4])
            if (opcode == 0x9) { pong(data); continue }
            if (opcode == 0x8) { open = false; return null }
            if (opcode != 0x1 && opcode != 0x2) continue
            return new String(data, StandardCharsets.UTF_8)
        }
    }
    private void pong(byte[] data) {
        ByteArrayOutputStream f = new ByteArrayOutputStream()
        f.write(0x8A); f.write(data.length); f.write(data)
        synchronized (out) { out.write(f.toByteArray()); out.flush() }
    }
    void close() { open = false; try { sock.close() } catch (Throwable ignored) {} }
}

// ---------- 一体服务端：GrS 自己就是 Socket 服务 + 控制终端 ----------
class DGLabLocalServer {
    final int port
    final String terminalId                 // 本地终端 ID（二维码里给 App 扫的）
    ServerSocket server
    volatile boolean running = false
    Thread acceptThread
    final ConcurrentHashMap<String, WsConn> apps = new ConcurrentHashMap<>()

    Closure onBind, onStatus, onFeedback, onLog

    DGLabLocalServer(int port) {
        this.port = port
        this.terminalId = UUID.randomUUID().toString().replace('-', '')
    }

    void start() {
        server = new ServerSocket(port)
        server.setReuseAddress(true)
        running = true
        acceptThread = new Thread({ acceptLoop() } as Runnable, 'DGLab-Accept')
        acceptThread.setDaemon(true); acceptThread.start()
        log("WS 服务端已启动 0.0.0.0:${port}，终端ID=${terminalId}")
    }

    private void acceptLoop() {
        while (running) {
            try {
                Socket s = server.accept()
                Thread t = new Thread({ handle(s) } as Runnable, 'DGLab-Conn')
                t.setDaemon(true); t.start()
            } catch (Exception e) { if (running) log('accept 异常: ' + e) }
        }
    }

    private void handle(Socket s) {
        WsConn c = new WsConn(s)
        String boundId = null
        try {
            String path = c.handshake()
            String seg = path.startsWith('/') ? path.substring(1).split('\\?')[0] : path
            if (seg && seg != terminalId) { log('拒绝未知 path: ' + path); c.close(); return }

            // 1) 给新连入的 App 分配它自己的 ID（targetId）
            String appId = UUID.randomUUID().toString().replace('-', '')
            c.sendJson([type: 'bind', clientId: appId, targetId: '', message: 'targetId'])

            // 2) 读 App 消息：bind(DGLAB) 建立映射 / msg 状态与反馈
            while (c.open && running) {
                String text = c.readText()
                if (text == null) break
                def o
                try { o = Json.parse(text) } catch (Throwable ignored) { continue }
                if (!(o instanceof Map)) continue
                String type = o.type as String
                if (type == 'bind') {
                    if (o.message == 'DGLAB') {
                        boundId = o.targetId as String ?: appId
                        apps[boundId] = c
                        c.sendJson([type: 'bind', clientId: o.clientId, targetId: boundId, message: '200'])
                        log("APP 已绑定 targetId=${boundId}")
                        if (onBind != null) onBind(boundId)
                    }
                } else if (type == 'msg') {
                    String m = o.message as String
                    if (m?.startsWith('strength-')) { log('强度同步 ' + m); if (onStatus != null) onStatus(m) }
                    else if (m?.startsWith('feedback-')) { log('按钮反馈 ' + m); if (onFeedback != null) onFeedback(m) }
                }
            }
        } catch (Exception e) {
            log('连接异常: ' + e)
        } finally {
            if (boundId) apps.remove(boundId, c)
            c.close()
        }
    }

    /** 向所有已绑定 App 下发业务 msg（4 字段齐全） */
    void sendMsg(String message) {
        apps.each { id, c ->
            if (c.open) c.sendJson([type: 'msg', clientId: terminalId, targetId: id, message: message])
        }
    }

    /** 生成官方二维码内容；lanIp 填局域网 IP（手机要和电脑同网段） */
    String getQrCode(String lanIp) {
        return "https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#ws://${lanIp}:${port}/${terminalId}"
    }

    void stop() {
        running = false
        try { server?.close() } catch (Throwable ignored) {}
        apps.values().each { it.close() }
        apps.clear()
    }
    void log(String s) { if (onLog != null) onLog('[DGLab] ' + s); else println '[DGLab] ' + s }
}

// ---------- 控制 API ----------
class DGLabCtrl {
    final DGLabLocalServer srv
    DGLabCtrl(DGLabLocalServer s) { srv = s }

    boolean isBound() { !srv.apps.isEmpty() }

    void addStrength(String ch, int v)    { srv.sendMsg("strength-${ch == 'A' ? 1 : 2}+1+${v}") }
    void reduceStrength(String ch, int v) { srv.sendMsg("strength-${ch == 'A' ? 1 : 2}+0+${v}") }
    void setStrength(String ch, int v)    { srv.sendMsg("strength-${ch == 'A' ? 1 : 2}+2+${v}") }
    void clearPulse(String ch)            { srv.sendMsg("clear-${ch == 'A' ? 1 : 2}") }

    /** hexFrames：8字节HEX帧，每帧100ms；自动按 80 帧分包以遵守 1950 字符上限 */
    void pulse(String ch, List<String> hexFrames) {
        if (!hexFrames) return
        int chunk = 80
        for (int i = 0; i < hexFrames.size(); i += chunk) {
            List<String> part = hexFrames.subList(i, Math.min(i + chunk, hexFrames.size()))
            srv.sendMsg("pulse-${ch}:" + Json.out(part))
            Thread.sleep((long)(100L * part.size()))
        }
    }

    /** 固定频率/强度波形帧：freqHz 10~1000，strength 0~100，frames 帧数 */
    static List<String> smoothPulse(double freqHz, int strength, int frames) {
        int periodMs = Math.max(10, (int) Math.round(1000.0 / freqHz))
        int a = Math.min(100, Math.max(1, (int)(periodMs * 0.1)))
        int gap = Math.max(0, periodMs - a)
        String hex = String.format('%02X%02X%02X%02X%02X%02X%02X%02X', a, 0, 0, 0, gap, 0, 0, 0)
        return (1..frames).collect { hex }
    }
}

// ================= 脚本主体：启动服务端并打印扫码链接 =================
// 端口与 config 无关，随便定（手机要能访问）。想换端口改这里。
def PORT = 5678
// 自动探测局域网 IP；探测不到就显示 127.0.0.1（此时手机连不上，请手动改）
def lanIp = java.net.NetworkInterface.getNetworkInterfaces().toList()
        .findAll { it.up }
        .collectMany { it.inetAddresses.toList() }
        .findAll { it instanceof java.net.Inet4Address && !it.loopbackAddress && !it.linkLocalAddress }
        .collect { it.hostAddress }
        .find { it.startsWith('192.168') || it.startsWith('10.') || it.startsWith('172.') } ?: '127.0.0.1'
// 存进 Properties，供 /dglabqr 指令生成二维码时使用
System.getProperties().put('dglab.lan.ip', lanIp)

// 热重载安全：先把上一次脚本运行留下的服务端关掉，避免 5678 端口被占用 / 重复实例 / 线程堆积。
// 用 JVM 级 System Properties 存实例，因为 GrS 重载会重新加载脚本类，脚本内的静态字段会被重置。
def SERVER_KEY = 'dglab.server.instance'
def CTRL_KEY = 'dglab.ctrl.instance'
def prev = System.getProperties().get(SERVER_KEY)
if (prev != null) {
    try { prev.stop() } catch (Throwable ignored) {}
}
def server = new DGLabLocalServer(PORT)
def ctrl = new DGLabCtrl(server)
System.getProperties().put(SERVER_KEY, server)
System.getProperties().put(CTRL_KEY, ctrl)
server.onLog = { String s -> println s }
server.start()
println '[DGLab] ===== 用 DG-LAB App 扫码连接 ====='
println server.getQrCode(lanIp)
println '[DGLab] 需要二维码图片时，在聊天栏输入 /dglabqr'
println '[DGLab] ================================='

// 事件示例（1.12.2 Forge 类名；需要 MC 类参与编译，在原版 GrS 环境直接放开即可）：
// eventManager.listen(net.minecraftforge.event.entity.living.LivingHurtEvent) { e ->
//     if (e.entity instanceof net.minecraft.entity.player.EntityPlayer && ctrl.bound) {
//         int s = Math.min(100, (int) Math.ceil((e.amount / 20f) * 100))
//         ctrl.addStrength('A', s)
//         ctrl.pulse('A', DGLabCtrl.smoothPulse(50, s, 10))
//     }
// }
// eventManager.listen(net.minecraftforge.event.entity.living.LivingDeathEvent) { e ->
//     if (e.entity instanceof net.minecraft.entity.player.EntityPlayer) {
//         ctrl.clearPulse('A'); ctrl.setStrength('A', 0); ctrl.setStrength('B', 0)
//     }
// }



// ==================== QR 编码器（nayuki, MIT，转译为 Groovy，前缀 DgQR_） ====================
// 用于把扫码链接编码成二维码矩阵；已在本地与 Java 原版逐位比对一致并通过 zxing 解码验证。
import java.nio.charset.StandardCharsets
import java.util.regex.Pattern


/* 
 * QR Code generator library (Java)
 * 
 * Copyright (c) Project Nayuki. (MIT License)
 * https://www.nayuki.io/page/qr-code-generator-library
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 * - The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 * - The Software is provided "as is", without warranty of any kind, express or
 *   implied, including but not limited to the warranties of merchantability,
 *   fitness for a particular purpose and noninfringement. In no event shall the
 *   authors or copyright holders be liable for any claim, damages or other
 *   liability, whether in an action of contract, tort or otherwise, arising from,
 *   out of or in connection with the Software or the use or other dealings in the
 *   Software.
 */




/**
 * An appendable sequence of bits (0s and 1s). Mainly used by {@link DgQR_QrSegment}.
 */
public final class DgQR_BitBuffer implements Cloneable {
	
	/*---- Fields ----*/
	
	private BitSet data;
	
	private int bitLength;  // Non-negative
	
	
	
	/*---- Constructor ----*/
	
	/**
	 * Constructs an empty bit buffer (length 0).
	 */
	public DgQR_BitBuffer() {
		data = new BitSet();
		bitLength = 0;
	}
	
	
	
	/*---- Methods ----*/
	
	/**
	 * Returns the length of this sequence, which is a non-negative value.
	 * @return the length of this sequence
	 */
	public int bitLength() {
		assert bitLength >= 0;
		return bitLength;
	}
	
	
	/**
	 * Returns the bit at the specified index, yielding 0 or 1.
	 * @param index the index to get the bit at
	 * @return the bit at the specified index
	 * @throws IndexOutOfBoundsException if index &lt; 0 or index &#x2265; bitLength
	 */
	public int getBit(int index) {
		if (index < 0 || index >= bitLength)
			throw new IndexOutOfBoundsException();
		return data.get(index) ? 1 : 0;
	}
	
	
	/**
	 * Appends the specified number of low-order bits of the specified value to this
	 * buffer. Requires 0 &#x2264; len &#x2264; 31 and 0 &#x2264; val &lt; 2<sup>len</sup>.
	 * @param val the value to append
	 * @param len the number of low-order bits in the value to take
	 * @throws IllegalArgumentException if the value or number of bits is out of range
	 * @throws IllegalStateException if appending the data
	 * would make bitLength exceed Integer.MAX_VALUE
	 */
	public void appendBits(int val, int len) {
		if (len < 0 || len > 31 || val >>> len != 0)
			throw new IllegalArgumentException("Value out of range");
		if (Integer.MAX_VALUE - bitLength < len)
			throw new IllegalStateException("Maximum length reached");
		for (int i = len - 1; i >= 0; i--, bitLength++)  // Append bit by bit
			data.set(bitLength, DgQR_QrCode.getBit(val, i));
	}
	
	
	/**
	 * Appends the content of the specified bit buffer to this buffer.
	 * @param bb the bit buffer whose data to append (not {@code null})
	 * @throws NullPointerException if the bit buffer is {@code null}
	 * @throws IllegalStateException if appending the data
	 * would make bitLength exceed Integer.MAX_VALUE
	 */
	public void appendData(DgQR_BitBuffer bb) {
		Objects.requireNonNull(bb);
		if (Integer.MAX_VALUE - bitLength < bb.bitLength)
			throw new IllegalStateException("Maximum length reached");
		for (int i = 0; i < bb.bitLength; i++, bitLength++)  // Append bit by bit
			data.set(bitLength, bb.data.get(i));
	}
	
	
	/**
	 * Returns a new copy of this buffer.
	 * @return a new copy of this buffer (not {@code null})
	 */
	public DgQR_BitBuffer clone() {
		try {
			DgQR_BitBuffer result = (DgQR_BitBuffer)super.clone();
			result.data = (BitSet)result.data.clone();
			return result;
		} catch (CloneNotSupportedException e) {
			throw new AssertionError(e);
		}
	}
	
}


/* 
 * QR Code generator library (Java)
 * 
 * Copyright (c) Project Nayuki. (MIT License)
 * https://www.nayuki.io/page/qr-code-generator-library
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 * - The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 * - The Software is provided "as is", without warranty of any kind, express or
 *   implied, including but not limited to the warranties of merchantability,
 *   fitness for a particular purpose and noninfringement. In no event shall the
 *   authors or copyright holders be liable for any claim, damages or other
 *   liability, whether in an action of contract, tort or otherwise, arising from,
 *   out of or in connection with the Software or the use or other dealings in the
 *   Software.
 */



/**
 * Thrown when the supplied data does not fit any QR Code version. Ways to handle this exception include:
 * <ul>
 *   <li><p>Decrease the error correction level if it was greater than {@code DgQR_Ecc.LOW}.</p></li>
 *   <li><p>If the advanced {@code encodeSegments()} function with 6 arguments or the
 *     {@code makeSegmentsOptimally()} function was called, then increase the maxVersion argument
 *     if it was less than {@link DgQR_QrCode#MAX_VERSION}. (This advice does not apply to the other
 *     factory functions because they search all versions up to {@code DgQR_QrCode.MAX_VERSION}.)</p></li>
 *   <li><p>Split the text data into better or optimal segments in order to reduce the number of
 *     bits required. (See {@link QrSegmentAdvanced#makeSegmentsOptimally(CharSequence,DgQR_QrCode.DgQR_Ecc,int,int)
 *     QrSegmentAdvanced.makeSegmentsOptimally()}.)</p></li>
 *   <li><p>Change the text or binary data to be shorter.</p></li>
 *   <li><p>Change the text to fit the character set of a particular segment mode (e.g. alphanumeric).</p></li>
 *   <li><p>Propagate the error upward to the caller/user.</p></li>
 * </ul>
 * @see DgQR_QrCode#encodeText(CharSequence, DgQR_QrCode.DgQR_Ecc)
 * @see DgQR_QrCode#encodeBinary(byte[], DgQR_QrCode.DgQR_Ecc)
 * @see DgQR_QrCode#encodeSegments(java.util.List, DgQR_QrCode.DgQR_Ecc)
 * @see DgQR_QrCode#encodeSegments(java.util.List, DgQR_QrCode.DgQR_Ecc, int, int, int, boolean)
 * @see QrSegmentAdvanced#makeSegmentsOptimally(CharSequence, DgQR_QrCode.DgQR_Ecc, int, int)
 */
public class DgQR_DataTooLongException extends IllegalArgumentException {
	
	public DgQR_DataTooLongException() {}
	
	
	public DgQR_DataTooLongException(String msg) {
		super(msg);
	}
	
}


/* 
 * QR Code generator library (Java)
 * 
 * Copyright (c) Project Nayuki. (MIT License)
 * https://www.nayuki.io/page/qr-code-generator-library
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 * - The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 * - The Software is provided "as is", without warranty of any kind, express or
 *   implied, including but not limited to the warranties of merchantability,
 *   fitness for a particular purpose and noninfringement. In no event shall the
 *   authors or copyright holders be liable for any claim, damages or other
 *   liability, whether in an action of contract, tort or otherwise, arising from,
 *   out of or in connection with the Software or the use or other dealings in the
 *   Software.
 */




/**
 * A segment of character/binary/control data in a QR Code symbol.
 * Instances of this class are immutable.
 * <p>The mid-level way to create a segment is to take the payload data and call a
 * static factory function such as {@link DgQR_QrSegment#makeNumeric(CharSequence)}. The low-level
 * way to create a segment is to custom-make the bit buffer and call the {@link
 * DgQR_QrSegment#DgQR_QrSegment(DgQR_Mode,int,DgQR_BitBuffer) constructor} with appropriate values.</p>
 * <p>This segment class imposes no length restrictions, but QR Codes have restrictions.
 * Even in the most favorable conditions, a QR Code can only hold 7089 characters of data.
 * Any segment longer than this is meaningless for the purpose of generating QR Codes.
 * This class can represent kanji mode segments, but provides no help in encoding them
 * - see {@link QrSegmentAdvanced} for full kanji support.</p>
 */
public final class DgQR_QrSegment {
	
	/*---- Static factory functions (mid level) ----*/
	
	/**
	 * Returns a segment representing the specified binary data
	 * encoded in byte mode. All input byte arrays are acceptable.
	 * <p>Any text string can be converted to UTF-8 bytes ({@code
	 * s.getBytes(StandardCharsets.UTF_8)}) and encoded as a byte mode segment.</p>
	 * @param data the binary data (not {@code null})
	 * @return a segment (not {@code null}) containing the data
	 * @throws NullPointerException if the array is {@code null}
	 */
	public static DgQR_QrSegment makeBytes(byte[] data) {
		Objects.requireNonNull(data);
		DgQR_BitBuffer bb = new DgQR_BitBuffer();
		for (byte b : data)
			bb.appendBits(b & 0xFF, 8);
		return new DgQR_QrSegment(DgQR_Mode.BYTE, data.length, bb);
	}
	
	
	/**
	 * Returns a segment representing the specified string of decimal digits encoded in numeric mode.
	 * @param digits the text (not {@code null}), with only digits from 0 to 9 allowed
	 * @return a segment (not {@code null}) containing the text
	 * @throws NullPointerException if the string is {@code null}
	 * @throws IllegalArgumentException if the string contains non-digit characters
	 */
	public static DgQR_QrSegment makeNumeric(CharSequence digits) {
		Objects.requireNonNull(digits);
		if (!isNumeric(digits))
			throw new IllegalArgumentException("String contains non-numeric characters");
		
		DgQR_BitBuffer bb = new DgQR_BitBuffer();
		for (int i = 0; i < digits.length(); ) {  // Consume up to 3 digits per iteration
			int n = Math.min(digits.length() - i, 3);
			bb.appendBits(Integer.parseInt(digits.subSequence(i, i + n).toString()), n * 3 + 1);
			i += n;
		}
		return new DgQR_QrSegment(DgQR_Mode.NUMERIC, digits.length(), bb);
	}
	
	
	/**
	 * Returns a segment representing the specified text string encoded in alphanumeric mode.
	 * The characters allowed are: 0 to 9, A to Z (uppercase only), space,
	 * dollar, percent, asterisk, plus, hyphen, period, slash, colon.
	 * @param text the text (not {@code null}), with only certain characters allowed
	 * @return a segment (not {@code null}) containing the text
	 * @throws NullPointerException if the string is {@code null}
	 * @throws IllegalArgumentException if the string contains non-encodable characters
	 */
	public static DgQR_QrSegment makeAlphanumeric(CharSequence text) {
		Objects.requireNonNull(text);
		if (!isAlphanumeric(text))
			throw new IllegalArgumentException("String contains unencodable characters in alphanumeric mode");
		
		DgQR_BitBuffer bb = new DgQR_BitBuffer();
		int i;
		for (i = 0; i <= text.length() - 2; i += 2) {  // Process groups of 2
			int temp = ALPHANUMERIC_CHARSET.indexOf(text.charAt(i)) * 45;
			temp += ALPHANUMERIC_CHARSET.indexOf(text.charAt(i + 1));
			bb.appendBits(temp, 11);
		}
		if (i < text.length())  // 1 character remaining
			bb.appendBits(ALPHANUMERIC_CHARSET.indexOf(text.charAt(i)), 6);
		return new DgQR_QrSegment(DgQR_Mode.ALPHANUMERIC, text.length(), bb);
	}
	
	
	/**
	 * Returns a list of zero or more segments to represent the specified Unicode text string.
	 * The result may use various segment modes and switch modes to optimize the length of the bit stream.
	 * @param text the text to be encoded, which can be any Unicode string
	 * @return a new mutable list (not {@code null}) of segments (not {@code null}) containing the text
	 * @throws NullPointerException if the text is {@code null}
	 */
	public static List<DgQR_QrSegment> makeSegments(CharSequence text) {
		Objects.requireNonNull(text);
		
		// Select the most efficient segment encoding automatically
		List<DgQR_QrSegment> result = new ArrayList<>();
		if (text.equals(""));  // Leave result empty
		else if (isNumeric(text))
			result.add(makeNumeric(text));
		else if (isAlphanumeric(text))
			result.add(makeAlphanumeric(text));
		else
			result.add(makeBytes(text.toString().getBytes(StandardCharsets.UTF_8)));
		return result;
	}
	
	
	/**
	 * Returns a segment representing an Extended Channel Interpretation
	 * (ECI) designator with the specified assignment value.
	 * @param assignVal the ECI assignment number (see the AIM ECI specification)
	 * @return a segment (not {@code null}) containing the data
	 * @throws IllegalArgumentException if the value is outside the range [0, 10<sup>6</sup>)
	 */
	public static DgQR_QrSegment makeEci(int assignVal) {
		DgQR_BitBuffer bb = new DgQR_BitBuffer();
		if (assignVal < 0)
			throw new IllegalArgumentException("ECI assignment value out of range");
		else if (assignVal < (1 << 7))
			bb.appendBits(assignVal, 8);
		else if (assignVal < (1 << 14)) {
			bb.appendBits(0b10, 2);
			bb.appendBits(assignVal, 14);
		} else if (assignVal < 1_000_000) {
			bb.appendBits(0b110, 3);
			bb.appendBits(assignVal, 21);
		} else
			throw new IllegalArgumentException("ECI assignment value out of range");
		return new DgQR_QrSegment(DgQR_Mode.ECI, 0, bb);
	}
	
	
	/**
	 * Tests whether the specified string can be encoded as a segment in numeric mode.
	 * A string is encodable iff each character is in the range 0 to 9.
	 * @param text the string to test for encodability (not {@code null})
	 * @return {@code true} iff each character is in the range 0 to 9.
	 * @throws NullPointerException if the string is {@code null}
	 * @see #makeNumeric(CharSequence)
	 */
	public static boolean isNumeric(CharSequence text) {
		return NUMERIC_REGEX.matcher(text).matches();
	}
	
	
	/**
	 * Tests whether the specified string can be encoded as a segment in alphanumeric mode.
	 * A string is encodable iff each character is in the following set: 0 to 9, A to Z
	 * (uppercase only), space, dollar, percent, asterisk, plus, hyphen, period, slash, colon.
	 * @param text the string to test for encodability (not {@code null})
	 * @return {@code true} iff each character is in the alphanumeric mode character set
	 * @throws NullPointerException if the string is {@code null}
	 * @see #makeAlphanumeric(CharSequence)
	 */
	public static boolean isAlphanumeric(CharSequence text) {
		return ALPHANUMERIC_REGEX.matcher(text).matches();
	}
	
	
	
	/*---- Instance fields ----*/
	
	/** The mode indicator of this segment. Not {@code null}. */
	public final DgQR_Mode mode;
	
	/** The length of this segment's unencoded data. Measured in characters for
	 * numeric/alphanumeric/kanji mode, bytes for byte mode, and 0 for ECI mode.
	 * Always zero or positive. Not the same as the data's bit length. */
	public final int numChars;
	
	// The data bits of this segment. Not null. Accessed through getData().
	final DgQR_BitBuffer data;
	
	
	/*---- Constructor (low level) ----*/
	
	/**
	 * Constructs a QR Code segment with the specified attributes and data.
	 * The character count (numCh) must agree with the mode and the bit buffer length,
	 * but the constraint isn't checked. The specified bit buffer is cloned and stored.
	 * @param md the mode (not {@code null})
	 * @param numCh the data length in characters or bytes, which is non-negative
	 * @param data the data bits (not {@code null})
	 * @throws NullPointerException if the mode or data is {@code null}
	 * @throws IllegalArgumentException if the character count is negative
	 */
	public DgQR_QrSegment(DgQR_Mode md, int numCh, DgQR_BitBuffer data) {
		mode = Objects.requireNonNull(md);
		Objects.requireNonNull(data);
		if (numCh < 0)
			throw new IllegalArgumentException("Invalid value");
		numChars = numCh;
		this.data = data.clone();  // Make defensive copy
	}
	
	
	/*---- Methods ----*/
	
	/**
	 * Returns the data bits of this segment.
	 * @return a new copy of the data bits (not {@code null})
	 */
	public DgQR_BitBuffer getData() {
		return data.clone();  // Make defensive copy
	}
	
	
	// Calculates the number of bits needed to encode the given segments at the given version.
	// Returns a non-negative number if successful. Otherwise returns -1 if a segment has too
	// many characters to fit its length field, or the total bits exceeds Integer.MAX_VALUE.
	static int getTotalBits(List<DgQR_QrSegment> segs, int version) {
		Objects.requireNonNull(segs);
		long result = 0;
		for (DgQR_QrSegment seg : segs) {
			Objects.requireNonNull(seg);
			int ccbits = seg.mode.numCharCountBits(version);
			if (seg.numChars >= (1 << ccbits))
				return -1;  // The segment's length doesn't fit the field's bit width
			result += 4L + ccbits + seg.data.bitLength();
			if (result > Integer.MAX_VALUE)
				return -1;  // The sum will overflow an int type
		}
		return (int)result;
	}
	
	
	/*---- Constants ----*/
	
	// Describes precisely all strings that are encodable in numeric mode.
	private static final Pattern NUMERIC_REGEX = Pattern.compile("[0-9]*");
	
	// Describes precisely all strings that are encodable in alphanumeric mode.
	private static final Pattern ALPHANUMERIC_REGEX = Pattern.compile("[A-Z0-9 \$%*+./:-]*");
	
	// The set of all legal characters in alphanumeric mode, where
	// each character value maps to the index in the string.
	static final String ALPHANUMERIC_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ \$%*+-./:";
	
	
	
	/*---- Public helper enumeration ----*/
	
	/**
	 * Describes how a segment's data bits are interpreted.
	 */
	public enum DgQR_Mode {
		
		/*-- Constants --*/
		
		NUMERIC     (0x1, 10, 12, 14),
		ALPHANUMERIC(0x2,  9, 11, 13),
		BYTE        (0x4,  8, 16, 16),
		KANJI       (0x8,  8, 10, 12),
		ECI         (0x7,  0,  0,  0);
		
		
		/*-- Fields --*/
		
		// The mode indicator bits, which is a uint4 value (range 0 to 15).
		final int modeBits;
		
		// Number of character count bits for three different version ranges.
		private final int[] numBitsCharCount;
		
		
		/*-- Constructor --*/
		
		private DgQR_Mode(int mode, int... ccbits) {
			modeBits = mode;
			numBitsCharCount = ccbits;
		}
		
		
		/*-- Method --*/
		
		// Returns the bit width of the character count field for a segment in this mode
		// in a QR Code at the given version number. The result is in the range [0, 16].
		int numCharCountBits(int ver) {
			assert DgQR_QrCode.MIN_VERSION <= ver && ver <= DgQR_QrCode.MAX_VERSION;
			return numBitsCharCount[(ver + 7).intdiv(17)];
		}
		
	}
	
}


/* 
 * QR Code generator library (Java)
 * 
 * Copyright (c) Project Nayuki. (MIT License)
 * https://www.nayuki.io/page/qr-code-generator-library
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 * - The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 * - The Software is provided "as is", without warranty of any kind, express or
 *   implied, including but not limited to the warranties of merchantability,
 *   fitness for a particular purpose and noninfringement. In no event shall the
 *   authors or copyright holders be liable for any claim, damages or other
 *   liability, whether in an action of contract, tort or otherwise, arising from,
 *   out of or in connection with the Software or the use or other dealings in the
 *   Software.
 */




/**
 * A QR Code symbol, which is a type of two-dimensional barcode.
 * Invented by Denso Wave and described in the ISO/IEC 18004 standard.
 * <p>Instances of this class represent an immutable square grid of dark and light cells.
 * The class provides static factory functions to create a QR Code from text or binary data.
 * The class covers the QR Code Model 2 specification, supporting all versions (sizes)
 * from 1 to 40, all 4 error correction levels, and 4 character encoding modes.</p>
 * <p>Ways to create a QR Code object:</p>
 * <ul>
 *   <li><p>High level: Take the payload data and call {@link DgQR_QrCode#encodeText(CharSequence,DgQR_Ecc)}
 *     or {@link DgQR_QrCode#encodeBinary(byte[],DgQR_Ecc)}.</p></li>
 *   <li><p>Mid level: Custom-make the list of {@link DgQR_QrSegment segments}
 *     and call {@link DgQR_QrCode#encodeSegments(List,DgQR_Ecc)} or
 *     {@link DgQR_QrCode#encodeSegments(List,DgQR_Ecc,int,int,int,boolean)}</p></li>
 *   <li><p>Low level: Custom-make the array of data codeword bytes (including segment headers and
 *     final padding, excluding error correction codewords), supply the appropriate version number,
 *     and call the {@link DgQR_QrCode#DgQR_QrCode(int,DgQR_Ecc,byte[],int) constructor}.</p></li>
 * </ul>
 * <p>(Note that all ways require supplying the desired error correction level.)</p>
 * @see DgQR_QrSegment
 */
public final class DgQR_QrCode {
	
	/*---- Static factory functions (high level) ----*/
	
	/**
	 * Returns a QR Code representing the specified Unicode text string at the specified error correction level.
	 * As a conservative upper bound, this function is guaranteed to succeed for strings that have 738 or fewer
	 * Unicode code points (not UTF-16 code units) if the low error correction level is used. The smallest possible
	 * QR Code version is automatically chosen for the output. The ECC level of the result may be higher than the
	 * ecl argument if it can be done without increasing the version.
	 * @param text the text to be encoded (not {@code null}), which can be any Unicode string
	 * @param ecl the error correction level to use (not {@code null}) (boostable)
	 * @return a QR Code (not {@code null}) representing the text
	 * @throws NullPointerException if the text or error correction level is {@code null}
	 * @throws DgQR_DataTooLongException if the text fails to fit in the
	 * largest version QR Code at the ECL, which means it is too long
	 */
	public static DgQR_QrCode encodeText(CharSequence text, DgQR_Ecc ecl) {
		Objects.requireNonNull(text);
		Objects.requireNonNull(ecl);
		List<DgQR_QrSegment> segs = DgQR_QrSegment.makeSegments(text);
		return encodeSegments(segs, ecl);
	}
	
	
	/**
	 * Returns a QR Code representing the specified binary data at the specified error correction level.
	 * This function always encodes using the binary segment mode, not any text mode. The maximum number of
	 * bytes allowed is 2953. The smallest possible QR Code version is automatically chosen for the output.
	 * The ECC level of the result may be higher than the ecl argument if it can be done without increasing the version.
	 * @param data the binary data to encode (not {@code null})
	 * @param ecl the error correction level to use (not {@code null}) (boostable)
	 * @return a QR Code (not {@code null}) representing the data
	 * @throws NullPointerException if the data or error correction level is {@code null}
	 * @throws DgQR_DataTooLongException if the data fails to fit in the
	 * largest version QR Code at the ECL, which means it is too long
	 */
	public static DgQR_QrCode encodeBinary(byte[] data, DgQR_Ecc ecl) {
		Objects.requireNonNull(data);
		Objects.requireNonNull(ecl);
		DgQR_QrSegment seg = DgQR_QrSegment.makeBytes(data);
		return encodeSegments(Arrays.asList(seg), ecl);
	}
	
	
	/*---- Static factory functions (mid level) ----*/
	
	/**
	 * Returns a QR Code representing the specified segments at the specified error correction
	 * level. The smallest possible QR Code version is automatically chosen for the output. The ECC level
	 * of the result may be higher than the ecl argument if it can be done without increasing the version.
	 * <p>This function allows the user to create a custom sequence of segments that switches
	 * between modes (such as alphanumeric and byte) to encode text in less space.
	 * This is a mid-level API; the high-level API is {@link #encodeText(CharSequence,DgQR_Ecc)}
	 * and {@link #encodeBinary(byte[],DgQR_Ecc)}.</p>
	 * @param segs the segments to encode
	 * @param ecl the error correction level to use (not {@code null}) (boostable)
	 * @return a QR Code (not {@code null}) representing the segments
	 * @throws NullPointerException if the list of segments, any segment, or the error correction level is {@code null}
	 * @throws DgQR_DataTooLongException if the segments fail to fit in the
	 * largest version QR Code at the ECL, which means they are too long
	 */
	public static DgQR_QrCode encodeSegments(List<DgQR_QrSegment> segs, DgQR_Ecc ecl) {
		return encodeSegments(segs, ecl, MIN_VERSION, MAX_VERSION, -1, true);
	}
	
	
	/**
	 * Returns a QR Code representing the specified segments with the specified encoding parameters.
	 * The smallest possible QR Code version within the specified range is automatically
	 * chosen for the output. Iff boostEcl is {@code true}, then the ECC level of the
	 * result may be higher than the ecl argument if it can be done without increasing
	 * the version. The mask number is either between 0 to 7 (inclusive) to force that
	 * mask, or &#x2212;1 to automatically choose an appropriate mask (which may be slow).
	 * <p>This function allows the user to create a custom sequence of segments that switches
	 * between modes (such as alphanumeric and byte) to encode text in less space.
	 * This is a mid-level API; the high-level API is {@link #encodeText(CharSequence,DgQR_Ecc)}
	 * and {@link #encodeBinary(byte[],DgQR_Ecc)}.</p>
	 * @param segs the segments to encode
	 * @param ecl the error correction level to use (not {@code null}) (boostable)
	 * @param minVersion the minimum allowed version of the QR Code (at least 1)
	 * @param maxVersion the maximum allowed version of the QR Code (at most 40)
	 * @param mask the mask number to use (between 0 and 7 (inclusive)), or &#x2212;1 for automatic mask
	 * @param boostEcl increases the ECC level as long as it doesn't increase the version number
	 * @return a QR Code (not {@code null}) representing the segments
	 * @throws NullPointerException if the list of segments, any segment, or the error correction level is {@code null}
	 * @throws IllegalArgumentException if 1 &#x2264; minVersion &#x2264; maxVersion &#x2264; 40
	 * or &#x2212;1 &#x2264; mask &#x2264; 7 is violated
	 * @throws DgQR_DataTooLongException if the segments fail to fit in
	 * the maxVersion QR Code at the ECL, which means they are too long
	 */
	public static DgQR_QrCode encodeSegments(List<DgQR_QrSegment> segs, DgQR_Ecc ecl, int minVersion, int maxVersion, int mask, boolean boostEcl) {
		Objects.requireNonNull(segs);
		Objects.requireNonNull(ecl);
		if (!(MIN_VERSION <= minVersion && minVersion <= maxVersion && maxVersion <= MAX_VERSION) || mask < -1 || mask > 7)
			throw new IllegalArgumentException("Invalid value");
		
		// Find the minimal version number to use
		int version, dataUsedBits;
		for (version = minVersion; ; version++) {
			int dataCapacityBits = getNumDataCodewords(version, ecl) * 8;  // Number of data bits available
			dataUsedBits = DgQR_QrSegment.getTotalBits(segs, version);
			if (dataUsedBits != -1 && dataUsedBits <= dataCapacityBits)
				break;  // This version number is found to be suitable
			if (version >= maxVersion) {  // All versions in the range could not fit the given data
				String msg = "Segment too long";
				if (dataUsedBits != -1)
					msg = String.format("Data length = %d bits, Max capacity = %d bits", dataUsedBits, dataCapacityBits);
				throw new DgQR_DataTooLongException(msg);
			}
		}
		assert dataUsedBits != -1;
		
		// Increase the error correction level while the data still fits in the current version number
		for (DgQR_Ecc newEcl : DgQR_Ecc.values()) {  // From low to high
			if (boostEcl && dataUsedBits <= getNumDataCodewords(version, newEcl) * 8)
				ecl = newEcl;
		}
		
		// Concatenate all segments to create the data bit string
		DgQR_BitBuffer bb = new DgQR_BitBuffer();
		for (DgQR_QrSegment seg : segs) {
			bb.appendBits(seg.mode.modeBits, 4);
			bb.appendBits(seg.numChars, seg.mode.numCharCountBits(version));
			bb.appendData(seg.data);
		}
		assert bb.bitLength() == dataUsedBits;
		
		// Add terminator and pad up to a byte if applicable
		int dataCapacityBits = getNumDataCodewords(version, ecl) * 8;
		assert bb.bitLength() <= dataCapacityBits;
		bb.appendBits(0, Math.min(4, dataCapacityBits - bb.bitLength()));
		bb.appendBits(0, (8 - bb.bitLength() % 8) % 8);
		assert bb.bitLength() % 8 == 0;
		
		// Pad with alternating bytes until data capacity is reached
		for (int padByte = 0xEC; bb.bitLength() < dataCapacityBits; padByte ^= 0xEC ^ 0x11)
			bb.appendBits(padByte, 8);
		
		// Pack bits into bytes in big endian
		byte[] dataCodewords = new byte[bb.bitLength().intdiv(8)];
		for (int i = 0; i < bb.bitLength(); i++)
			dataCodewords[i >>> 3] |= bb.getBit(i) << (7 - (i & 7));
		
		// Create the QR Code object
		return new DgQR_QrCode(version, ecl, dataCodewords, mask);
	}
	
	
	
	/*---- Instance fields ----*/
	
	// Public immutable scalar parameters:
	
	/** The version number of this QR Code, which is between 1 and 40 (inclusive).
	 * This determines the size of this barcode. */
	public final int version;
	
	/** The width and height of this QR Code, measured in modules, between
	 * 21 and 177 (inclusive). This is equal to version &#xD7; 4 + 17. */
	public final int size;
	
	/** The error correction level used in this QR Code, which is not {@code null}. */
	public final DgQR_Ecc errorCorrectionLevel;
	
	/** The index of the mask pattern used in this QR Code, which is between 0 and 7 (inclusive).
	 * <p>Even if a QR Code is created with automatic masking requested (mask =
	 * &#x2212;1), the resulting object still has a mask value between 0 and 7. */
	public final int mask;
	
	// Private grids of modules/pixels, with dimensions of size*size:
	
	// The modules of this QR Code (false = light, true = dark).
	// Immutable after constructor finishes. Accessed through getModule().
	private boolean[][] modules;
	
	// Indicates function modules that are not subjected to masking. Discarded when constructor finishes.
	private boolean[][] isFunction;
	
	
	
	/*---- Constructor (low level) ----*/
	
	/**
	 * Constructs a QR Code with the specified version number,
	 * error correction level, data codeword bytes, and mask number.
	 * <p>This is a low-level API that most users should not use directly. A mid-level
	 * API is the {@link #encodeSegments(List,DgQR_Ecc,int,int,int,boolean)} function.</p>
	 * @param ver the version number to use, which must be in the range 1 to 40 (inclusive)
	 * @param ecl the error correction level to use
	 * @param dataCodewords the bytes representing segments to encode (without ECC)
	 * @param msk the mask pattern to use, which is either &#x2212;1 for automatic choice or from 0 to 7 for fixed choice
	 * @throws NullPointerException if the byte array or error correction level is {@code null}
	 * @throws IllegalArgumentException if the version or mask value is out of range,
	 * or if the data is the wrong length for the specified version and error correction level
	 */
	public DgQR_QrCode(int ver, DgQR_Ecc ecl, byte[] dataCodewords, int msk) {
		// Check arguments and initialize fields
		if (ver < MIN_VERSION || ver > MAX_VERSION)
			throw new IllegalArgumentException("Version value out of range");
		if (msk < -1 || msk > 7)
			throw new IllegalArgumentException("Mask value out of range");
		version = ver;
		size = ver * 4 + 17;
		errorCorrectionLevel = Objects.requireNonNull(ecl);
		Objects.requireNonNull(dataCodewords);
		modules    = new boolean[size][size];  // Initially all light
		isFunction = new boolean[size][size];
		
		// Compute ECC, draw modules, do masking
		drawFunctionPatterns();
		byte[] allCodewords = addEccAndInterleave(dataCodewords);
		drawCodewords(allCodewords);
		
		// Do masking
		if (msk == -1) {  // Automatically choose best mask
			int minPenalty = Integer.MAX_VALUE;
			for (int i = 0; i < 8; i++) {
				applyMask(i);
				drawFormatBits(i);
				int penalty = getPenaltyScore();
				if (penalty < minPenalty) {
					msk = i;
					minPenalty = penalty;
				}
				applyMask(i);  // Undoes the mask due to XOR
			}
		}
		assert 0 <= msk && msk <= 7;
		mask = msk;
		applyMask(msk);  // Apply the final choice of mask
		drawFormatBits(msk);  // Overwrite old format bits
		
		isFunction = null;
	}
	
	
	
	/*---- Public instance methods ----*/
	
	/**
	 * Returns the color of the module (pixel) at the specified coordinates, which is {@code false}
	 * for light or {@code true} for dark. The top left corner has the coordinates (x=0, y=0).
	 * If the specified coordinates are out of bounds, then {@code false} (light) is returned.
	 * @param x the x coordinate, where 0 is the left edge and size&#x2212;1 is the right edge
	 * @param y the y coordinate, where 0 is the top edge and size&#x2212;1 is the bottom edge
	 * @return {@code true} if the coordinates are in bounds and the module
	 * at that location is dark, or {@code false} (light) otherwise
	 */
	public boolean getModule(int x, int y) {
		return 0 <= x && x < size && 0 <= y && y < size && modules[y][x];
	}
	
	
	
	/*---- Private helper methods for constructor: Drawing function modules ----*/
	
	// Reads this object's version field, and draws and marks all function modules.
	private void drawFunctionPatterns() {
		// Draw horizontal and vertical timing patterns
		for (int i = 0; i < size; i++) {
			setFunctionModule(6, i, i % 2 == 0);
			setFunctionModule(i, 6, i % 2 == 0);
		}
		
		// Draw 3 finder patterns (all corners except bottom right; overwrites some timing modules)
		drawFinderPattern(3, 3);
		drawFinderPattern(size - 4, 3);
		drawFinderPattern(3, size - 4);
		
		// Draw numerous alignment patterns
		int[] alignPatPos = getAlignmentPatternPositions();
		int numAlign = alignPatPos.length;
		for (int i = 0; i < numAlign; i++) {
			for (int j = 0; j < numAlign; j++) {
				// Don't draw on the three finder corners
				if (!(i == 0 && j == 0 || i == 0 && j == numAlign - 1 || i == numAlign - 1 && j == 0))
					drawAlignmentPattern(alignPatPos[i], alignPatPos[j]);
			}
		}
		
		// Draw configuration data
		drawFormatBits(0);  // Dummy mask value; overwritten later in the constructor
		drawVersion();
	}
	
	
	// Draws two copies of the format bits (with its own error correction code)
	// based on the given mask and this object's error correction level field.
	private void drawFormatBits(int msk) {
		// Calculate error correction code and pack bits
		int data = errorCorrectionLevel.formatBits << 3 | msk;  // errCorrLvl is uint2, mask is uint3
		int rem = data;
		for (int i = 0; i < 10; i++)
			rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
		int bits = (data << 10 | rem) ^ 0x5412;  // uint15
		assert bits >>> 15 == 0;
		
		// Draw first copy
		for (int i = 0; i <= 5; i++)
			setFunctionModule(8, i, getBit(bits, i));
		setFunctionModule(8, 7, getBit(bits, 6));
		setFunctionModule(8, 8, getBit(bits, 7));
		setFunctionModule(7, 8, getBit(bits, 8));
		for (int i = 9; i < 15; i++)
			setFunctionModule(14 - i, 8, getBit(bits, i));
		
		// Draw second copy
		for (int i = 0; i < 8; i++)
			setFunctionModule(size - 1 - i, 8, getBit(bits, i));
		for (int i = 8; i < 15; i++)
			setFunctionModule(8, size - 15 + i, getBit(bits, i));
		setFunctionModule(8, size - 8, true);  // Always dark
	}
	
	
	// Draws two copies of the version bits (with its own error correction code),
	// based on this object's version field, iff 7 <= version <= 40.
	private void drawVersion() {
		if (version < 7)
			return;
		
		// Calculate error correction code and pack bits
		int rem = version;  // version is uint6, in the range [7, 40]
		for (int i = 0; i < 12; i++)
			rem = (rem << 1) ^ ((rem >>> 11) * 0x1F25);
		int bits = version << 12 | rem;  // uint18
		assert bits >>> 18 == 0;
		
		// Draw two copies
		for (int i = 0; i < 18; i++) {
			boolean bit = getBit(bits, i);
			int a = size - 11 + i % 3;
			int b = i.intdiv(3);
			setFunctionModule(a, b, bit);
			setFunctionModule(b, a, bit);
		}
	}
	
	
	// Draws a 9*9 finder pattern including the border separator,
	// with the center module at (x, y). Modules can be out of bounds.
	private void drawFinderPattern(int x, int y) {
		for (int dy = -4; dy <= 4; dy++) {
			for (int dx = -4; dx <= 4; dx++) {
				int dist = Math.max(Math.abs(dx), Math.abs(dy));  // Chebyshev/infinity norm
				int xx = x + dx, yy = y + dy;
				if (0 <= xx && xx < size && 0 <= yy && yy < size)
					setFunctionModule(xx, yy, dist != 2 && dist != 4);
			}
		}
	}
	
	
	// Draws a 5*5 alignment pattern, with the center module
	// at (x, y). All modules must be in bounds.
	private void drawAlignmentPattern(int x, int y) {
		for (int dy = -2; dy <= 2; dy++) {
			for (int dx = -2; dx <= 2; dx++)
				setFunctionModule(x + dx, y + dy, Math.max(Math.abs(dx), Math.abs(dy)) != 1);
		}
	}
	
	
	// Sets the color of a module and marks it as a function module.
	// Only used by the constructor. Coordinates must be in bounds.
	private void setFunctionModule(int x, int y, boolean isDark) {
		modules[y][x] = isDark;
		isFunction[y][x] = true;
	}
	
	
	/*---- Private helper methods for constructor: Codewords and masking ----*/
	
	// Returns a new byte string representing the given data with the appropriate error correction
	// codewords appended to it, based on this object's version and error correction level.
	private byte[] addEccAndInterleave(byte[] data) {
		Objects.requireNonNull(data);
		if (data.length != getNumDataCodewords(version, errorCorrectionLevel))
			throw new IllegalArgumentException();
		
		// Calculate parameter numbers
		int numBlocks = NUM_ERROR_CORRECTION_BLOCKS[errorCorrectionLevel.ordinal()][version];
		int blockEccLen = ECC_CODEWORDS_PER_BLOCK  [errorCorrectionLevel.ordinal()][version];
		int rawCodewords = getNumRawDataModules(version).intdiv(8);
		int numShortBlocks = numBlocks - rawCodewords % numBlocks;
		int shortBlockLen = rawCodewords.intdiv(numBlocks);
		
		// Split data into blocks and append ECC to each block
		byte[][] blocks = new byte[numBlocks][];
		byte[] rsDiv = reedSolomonComputeDivisor(blockEccLen);
		for (int i = 0, k = 0; i < numBlocks; i++) {
			byte[] dat = Arrays.copyOfRange(data, k, k + shortBlockLen - blockEccLen + (i < numShortBlocks ? 0 : 1));
			k += dat.length;
			byte[] block = Arrays.copyOf(dat, shortBlockLen + 1);
			byte[] ecc = reedSolomonComputeRemainder(dat, rsDiv);
			System.arraycopy(ecc, 0, block, block.length - blockEccLen, ecc.length);
			blocks[i] = block;
		}
		
		// Interleave (not concatenate) the bytes from every block into a single sequence
		byte[] result = new byte[rawCodewords];
		for (int i = 0, k = 0; i < blocks[0].length; i++) {
			for (int j = 0; j < blocks.length; j++) {
				// Skip the padding byte in short blocks
				if (i != shortBlockLen - blockEccLen || j >= numShortBlocks) {
					result[k] = blocks[j][i];
					k++;
				}
			}
		}
		return result;
	}
	
	
	// Draws the given sequence of 8-bit codewords (data and error correction) onto the entire
	// data area of this QR Code. Function modules need to be marked off before this is called.
	private void drawCodewords(byte[] data) {
		Objects.requireNonNull(data);
		if (data.length != getNumRawDataModules(version).intdiv(8))
			throw new IllegalArgumentException();
		
		int i = 0;  // Bit index into the data
		// Do the funny zigzag scan
		for (int right = size - 1; right >= 1; right -= 2) {  // Index of right column in each column pair
			if (right == 6)
				right = 5;
			for (int vert = 0; vert < size; vert++) {  // Vertical counter
				for (int j = 0; j < 2; j++) {
					int x = right - j;  // Actual x coordinate
					boolean upward = ((right + 1) & 2) == 0;
					int y = upward ? size - 1 - vert : vert;  // Actual y coordinate
					if (!isFunction[y][x] && i < data.length * 8) {
						modules[y][x] = getBit(data[i >>> 3], 7 - (i & 7));
						i++;
					}
					// If this QR Code has any remainder bits (0 to 7), they were assigned as
					// 0/false/light by the constructor and are left unchanged by this method
				}
			}
		}
		assert i == data.length * 8;
	}
	
	
	// XORs the codeword modules in this QR Code with the given mask pattern.
	// The function modules must be marked and the codeword bits must be drawn
	// before masking. Due to the arithmetic of XOR, calling applyMask() with
	// the same mask value a second time will undo the mask. A final well-formed
	// QR Code needs exactly one (not zero, two, etc.) mask applied.
	private void applyMask(int msk) {
		if (msk < 0 || msk > 7)
			throw new IllegalArgumentException("Mask value out of range");
		for (int y = 0; y < size; y++) {
			for (int x = 0; x < size; x++) {
				boolean invert;
				switch (msk) {
					case 0:  invert = (x + y) % 2 == 0;                    break;
					case 1:  invert = y % 2 == 0;                          break;
					case 2:  invert = x % 3 == 0;                          break;
					case 3:  invert = (x + y) % 3 == 0;                    break;
					case 4:  invert = (x / 3 + y.intdiv(2)) % 2 == 0;            break;
					case 5:  invert = x * y % 2 + x * y % 3 == 0;          break;
					case 6:  invert = (x * y % 2 + x * y % 3) % 2 == 0;    break;
					case 7:  invert = ((x + y) % 2 + x * y % 3) % 2 == 0;  break;
					default:  throw new AssertionError();
				}
				modules[y][x] ^= invert & !isFunction[y][x];
			}
		}
	}
	
	
	// Calculates and returns the penalty score based on state of this QR Code's current modules.
	// This is used by the automatic mask choice algorithm to find the mask pattern that yields the lowest score.
	private int getPenaltyScore() {
		int result = 0;
		
		// Adjacent modules in row having same color, and finder-like patterns
		for (int y = 0; y < size; y++) {
			boolean runColor = false;
			int runX = 0;
			int[] runHistory = new int[7];
			for (int x = 0; x < size; x++) {
				if (modules[y][x] == runColor) {
					runX++;
					if (runX == 5)
						result += PENALTY_N1;
					else if (runX > 5)
						result++;
				} else {
					finderPenaltyAddHistory(runX, runHistory);
					if (!runColor)
						result += finderPenaltyCountPatterns(runHistory) * PENALTY_N3;
					runColor = modules[y][x];
					runX = 1;
				}
			}
			result += finderPenaltyTerminateAndCount(runColor, runX, runHistory) * PENALTY_N3;
		}
		// Adjacent modules in column having same color, and finder-like patterns
		for (int x = 0; x < size; x++) {
			boolean runColor = false;
			int runY = 0;
			int[] runHistory = new int[7];
			for (int y = 0; y < size; y++) {
				if (modules[y][x] == runColor) {
					runY++;
					if (runY == 5)
						result += PENALTY_N1;
					else if (runY > 5)
						result++;
				} else {
					finderPenaltyAddHistory(runY, runHistory);
					if (!runColor)
						result += finderPenaltyCountPatterns(runHistory) * PENALTY_N3;
					runColor = modules[y][x];
					runY = 1;
				}
			}
			result += finderPenaltyTerminateAndCount(runColor, runY, runHistory) * PENALTY_N3;
		}
		
		// 2*2 blocks of modules having same color
		for (int y = 0; y < size - 1; y++) {
			for (int x = 0; x < size - 1; x++) {
				boolean color = modules[y][x];
				if (  color == modules[y][x + 1] &&
				      color == modules[y + 1][x] &&
				      color == modules[y + 1][x + 1])
					result += PENALTY_N2;
			}
		}
		
		// Balance of dark and light modules
		int dark = 0;
		for (boolean[] row : modules) {
			for (boolean color : row) {
				if (color)
					dark++;
			}
		}
		int total = size * size;  // Note that size is odd, so dark/total != 1/2
		// Compute the smallest integer k >= 0 such that (45-5k)% <= dark/total <= (55+5k)%
		int k = (Math.abs(dark * 20 - total * 10) + total - 1).intdiv(total) - 1;
		assert 0 <= k && k <= 9;
		result += k * PENALTY_N4;
		assert 0 <= result && result <= 2568888;  // Non-tight upper bound based on default values of PENALTY_N1, ..., N4
		return result;
	}
	
	
	
	/*---- Private helper functions ----*/
	
	// Returns an ascending list of positions of alignment patterns for this version number.
	// Each position is in the range [0,177), and are used on both the x and y axes.
	// This could be implemented as lookup table of 40 variable-length lists of unsigned bytes.
	private int[] getAlignmentPatternPositions() {
		if (version == 1)
			return new int[]{};
		else {
			int numAlign = version.intdiv(7) + 2;
			int step = (version * 8 + numAlign * 3 + 5).intdiv(numAlign * 4 - 4) * 2;
			int[] result = new int[numAlign];
			result[0] = 6;
			for (int i = result.length - 1, pos = size - 7; i >= 1; i--, pos -= step)
				result[i] = pos;
			return result;
		}
	}
	
	
	// Returns the number of data bits that can be stored in a QR Code of the given version number, after
	// all function modules are excluded. This includes remainder bits, so it might not be a multiple of 8.
	// The result is in the range [208, 29648]. This could be implemented as a 40-entry lookup table.
	private static int getNumRawDataModules(int ver) {
		if (ver < MIN_VERSION || ver > MAX_VERSION)
			throw new IllegalArgumentException("Version number out of range");
		
		int size = ver * 4 + 17;
		int result = size * size;   // Number of modules in the whole QR Code square
		result -= 8 * 8 * 3;        // Subtract the three finders with separators
		result -= 15 * 2 + 1;       // Subtract the format information and dark module
		result -= (size - 16) * 2;  // Subtract the timing patterns (excluding finders)
		// The five lines above are equivalent to: int result = (16 * ver + 128) * ver + 64;
		if (ver >= 2) {
			int numAlign = ver.intdiv(7) + 2;
			result -= (numAlign - 1) * (numAlign - 1) * 25;  // Subtract alignment patterns not overlapping with timing patterns
			result -= (numAlign - 2) * 2 * 20;  // Subtract alignment patterns that overlap with timing patterns
			// The two lines above are equivalent to: result -= (25 * numAlign - 10) * numAlign - 55;
			if (ver >= 7)
				result -= 6 * 3 * 2;  // Subtract version information
		}
		assert 208 <= result && result <= 29648;
		return result;
	}
	
	
	// Returns a Reed-Solomon ECC generator polynomial for the given degree. This could be
	// implemented as a lookup table over all possible parameter values, instead of as an algorithm.
	private static byte[] reedSolomonComputeDivisor(int degree) {
		if (degree < 1 || degree > 255)
			throw new IllegalArgumentException("Degree out of range");
		// Polynomial coefficients are stored from highest to lowest power, excluding the leading term which is always 1.
		// For example the polynomial x^3 + 255x^2 + 8x + 93 is stored as the uint8 array {255, 8, 93}.
		byte[] result = new byte[degree];
		result[degree - 1] = 1;  // Start off with the monomial x^0
		
		// Compute the product polynomial (x - r^0) * (x - r^1) * (x - r^2) * ... * (x - r^{degree-1}),
		// and drop the highest monomial term which is always 1x^degree.
		// Note that r = 0x02, which is a generator element of this field GF(2^8/0x11D).
		int root = 1;
		for (int i = 0; i < degree; i++) {
			// Multiply the current product by (x - r^i)
			for (int j = 0; j < result.length; j++) {
				result[j] = (byte)reedSolomonMultiply(result[j] & 0xFF, root);
				if (j + 1 < result.length)
					result[j] ^= result[j + 1];
			}
			root = reedSolomonMultiply(root, 0x02);
		}
		return result;
	}
	
	
	// Returns the Reed-Solomon error correction codeword for the given data and divisor polynomials.
	private static byte[] reedSolomonComputeRemainder(byte[] data, byte[] divisor) {
		Objects.requireNonNull(data);
		Objects.requireNonNull(divisor);
		byte[] result = new byte[divisor.length];
		for (byte b : data) {  // Polynomial division
			int factor = (b ^ result[0]) & 0xFF;
			System.arraycopy(result, 1, result, 0, result.length - 1);
			result[result.length - 1] = 0;
			for (int i = 0; i < result.length; i++)
				result[i] ^= reedSolomonMultiply(divisor[i] & 0xFF, factor);
		}
		return result;
	}
	
	
	// Returns the product of the two given field elements modulo GF(2^8/0x11D). The arguments and result
	// are unsigned 8-bit integers. This could be implemented as a lookup table of 256*256 entries of uint8.
	private static int reedSolomonMultiply(int x, int y) {
		assert x >> 8 == 0 && y >> 8 == 0;
		// Russian peasant multiplication
		int z = 0;
		for (int i = 7; i >= 0; i--) {
			z = (z << 1) ^ ((z >>> 7) * 0x11D);
			z ^= ((y >>> i) & 1) * x;
		}
		assert z >>> 8 == 0;
		return z;
	}
	
	
	// Returns the number of 8-bit data (i.e. not error correction) codewords contained in any
	// QR Code of the given version number and error correction level, with remainder bits discarded.
	// This stateless pure function could be implemented as a (40*4)-cell lookup table.
	static int getNumDataCodewords(int ver, DgQR_Ecc ecl) {
		return (getNumRawDataModules(ver).intdiv(8) - ECC_CODEWORDS_PER_BLOCK[ecl.ordinal()][ver] * NUM_ERROR_CORRECTION_BLOCKS[ecl.ordinal()][ver]);
	}
	
	
	// Can only be called immediately after a light run is added, and
	// returns either 0, 1, or 2. A helper function for getPenaltyScore().
	private int finderPenaltyCountPatterns(int[] runHistory) {
		int n = runHistory[1];
		assert n <= size * 3;
		boolean core = n > 0 && runHistory[2] == n && runHistory[3] == n * 3 && runHistory[4] == n && runHistory[5] == n;
		return (core && runHistory[0] >= n * 4 && runHistory[6] >= n ? 1 : 0)
		     + (core && runHistory[6] >= n * 4 && runHistory[0] >= n ? 1 : 0);
	}
	
	
	// Must be called at the end of a line (row or column) of modules. A helper function for getPenaltyScore().
	private int finderPenaltyTerminateAndCount(boolean currentRunColor, int currentRunLength, int[] runHistory) {
		if (currentRunColor) {  // Terminate dark run
			finderPenaltyAddHistory(currentRunLength, runHistory);
			currentRunLength = 0;
		}
		currentRunLength += size;  // Add light border to final run
		finderPenaltyAddHistory(currentRunLength, runHistory);
		return finderPenaltyCountPatterns(runHistory);
	}
	
	
	// Pushes the given value to the front and drops the last value. A helper function for getPenaltyScore().
	private void finderPenaltyAddHistory(int currentRunLength, int[] runHistory) {
		if (runHistory[0] == 0)
			currentRunLength += size;  // Add light border to initial run
		System.arraycopy(runHistory, 0, runHistory, 1, runHistory.length - 1);
		runHistory[0] = currentRunLength;
	}
	
	
	// Returns true iff the i'th bit of x is set to 1.
	static boolean getBit(int x, int i) {
		return ((x >>> i) & 1) != 0;
	}
	
	
	/*---- Constants and tables ----*/
	
	/** The minimum version number  (1) supported in the QR Code Model 2 standard. */
	public static final int MIN_VERSION =  1;
	
	/** The maximum version number (40) supported in the QR Code Model 2 standard. */
	public static final int MAX_VERSION = 40;
	
	
	// For use in getPenaltyScore(), when evaluating which mask is best.
	private static final int PENALTY_N1 =  3;
	private static final int PENALTY_N2 =  3;
	private static final int PENALTY_N3 = 40;
	private static final int PENALTY_N4 = 10;
	
	
	private static final byte[][] ECC_CODEWORDS_PER_BLOCK = [
		// Version: (note that index 0 is for padding, and is set to an illegal value)
		//0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
		[-1,  7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],  // Low
		[-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],  // Medium
		[-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],  // Quartile
		[-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],  // High
	];
	
	private static final byte[][] NUM_ERROR_CORRECTION_BLOCKS = [
		// Version: (note that index 0 is for padding, and is set to an illegal value)
		//0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40    Error correction level
		[-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4,  4,  4,  4,  4,  6,  6,  6,  6,  7,  8,  8,  9,  9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],  // Low
		[-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5,  5,  8,  9,  9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],  // Medium
		[-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8,  8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],  // Quartile
		[-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81],  // High
	];
	
	
	
	/*---- Public helper enumeration ----*/
	
	/**
	 * The error correction level in a QR Code symbol.
	 */
	public enum DgQR_Ecc {
		// Must be declared in ascending order of error protection
		// so that the implicit ordinal() and values() work properly
		/** The QR Code can tolerate about  7% erroneous codewords. */ LOW(1),
		/** The QR Code can tolerate about 15% erroneous codewords. */ MEDIUM(0),
		/** The QR Code can tolerate about 25% erroneous codewords. */ QUARTILE(3),
		/** The QR Code can tolerate about 30% erroneous codewords. */ HIGH(2);
		
		// In the range 0 to 3 (unsigned 2-bit integer).
		final int formatBits;
		
		// Constructor.
		private DgQR_Ecc(int fb) {
			formatBits = fb;
		}
	}
	
}


// ==================== 二维码图片生成 + 系统默认程序打开 ====================
// 生成 PNG 图片（JDK 自带 BufferedImage/ImageIO），用系统默认程序打开，
// 彻底避开日志等宽字体错位导致扫不了的问题。
// 用静态类而不是闭包：类定义是编译期的，避免脚本「先调用后定义」的时序问题。
class DgQrImage {
    static void writeAndOpen(String text) {
        // 用编译期直接类名引用，不走 Class.forName（GrS 沙箱会拦运行期类查找）
        def qr = DgQR_QrCode.encodeText(text, DgQR_QrCode.DgQR_Ecc.MEDIUM)
        int n = qr.size
        int quiet = 4            // 静默区（模块数）
        int scale = 10           // 每模块像素
        int side = (n + quiet * 2) * scale

        def img = new java.awt.image.BufferedImage(side, side, java.awt.image.BufferedImage.TYPE_INT_RGB)
        def g = img.createGraphics()
        g.setColor(java.awt.Color.WHITE)
        g.fillRect(0, 0, side, side)
        g.setColor(java.awt.Color.BLACK)
        for (int row = 0; row < n; row++) {
            for (int col = 0; col < n; col++) {
                if (qr.getModule(col, row)) {
                    g.fillRect((col + quiet) * scale, (row + quiet) * scale, scale, scale)
                }
            }
        }
        g.dispose()

        // 关键：GrS 沙箱在编译期把脚本里的 new File(...) 换成它自己的 GroovyFile，
        // 一旦用 java.io.File 类型接收/强转就抛 GroovyCastException。
        // 所以全程用「字符串路径 + NIO 写字节」，完全不碰 java.io.File。
        String dirPath = System.getProperty('user.dir').toString()   // GroovyFile.toString() = 路径
        String outPath = dirPath + '/dglab_qr.png'

        // 先把图片编码到内存字节流（ImageIO 的 OutputStream 重载，不接 File）
        def baos = new ByteArrayOutputStream()
        javax.imageio.ImageIO.write(img, 'png', baos)
        byte[] bytes = baos.toByteArray()

        // 写文件：多种方式兜底，都不用 java.io.File
        boolean written = false
        try {
            java.nio.file.Files.write(java.nio.file.Paths.get(outPath), bytes)
            written = true
        } catch (Throwable ignored) {}
        if (!written) {
            try {
                def fos = new FileOutputStream(outPath)
                fos.write(bytes); fos.close()
                written = true
            } catch (Throwable ignored) {}
        }
        if (!written) {
            println '[DGLab] 二维码图片写入失败，路径: ' + outPath
            return
        }
        println '[DGLab] 二维码图片已生成: ' + outPath

        // 用系统默认程序打开：ProcessBuilder(cmd start) 绕开 Desktop.open(File)
        try {
            new ProcessBuilder('cmd', '/c', 'start', '""', '"' + outPath + '"').start()
            println '[DGLab] 已用系统默认程序打开二维码图片，请用 DG-LAB App 扫码'
        } catch (Throwable t) {
            println '[DGLab] 自动打开失败，请手动打开: ' + outPath + ' (' + t + ')'
        }
    }
}

// ==================== /dglabqr 指令：手动打开二维码图片 ====================
// 不再每次 reload 自动弹图片，改成需要时聊天栏输入 /dglabqr
def showQr = {
    try {
        def s = System.getProperties().get('dglab.server.instance')
        def ip = System.getProperties().get('dglab.lan.ip') ?: '127.0.0.1'
        if (s == null) { println '[DGLab] 服务端未启动，无法生成二维码'; return }
        DgQrImage.writeAndOpen(s.getQrCode(ip.toString()))
    } catch (Throwable t) {
        println '[DGLab] 生成二维码失败: ' + t
    }
}

// 入口1：客户端命令
mods.minecraft.command.registerClientCommand('dglabqr', '/dglabqr - 打开 DG-LAB 二维码图片') { s, sender, args ->
    net.minecraft.client.Minecraft.getMinecraft().addScheduledTask({ showQr() } as Runnable)
}
// 入口2：拦截聊天输入（GrS 事件闭包无参 + delegate=事件对象）
eventManager.listen(net.minecraftforge.client.event.ClientChatEvent) {
    if (message?.trim()?.toLowerCase() == '/dglabqr') {
        setCanceled(true)
        net.minecraft.client.Minecraft.getMinecraft().addScheduledTask({ showQr() } as Runnable)
    }
}

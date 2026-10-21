#!/usr/bin/env python3
"""《大决战 · 回信》求解程序。

命题方的回信沿用"大决战"的七层框架：每层解出一个整数种子，以 SHAKE-256(str(种子)) 为密钥流与下一层密文异或，
得到"下一层参数头 + \\n--RAW--\\n + 更内层密文"；第七层之后为明文，其 SHA-256 须等于卷首 commitment。

与原版"大决战"相比有两处不同（见 epilogue/README.md）：
  · L1 时间锁：y = lock^(2^T) mod n（原版为 2^(2^T) mod n），种子 = (lock − y) mod n；
  · L3 的 p+1 含大于 70000 的素数幂，平滑上界需放大到 5×10^6。

用法：python3 epilogue/solve_grandmaster_reply.py [epilogue/grandmaster_reply.txt]
可选依赖 gmpy2（L3 提速约 10 倍）；没有也能运行。
"""
import base64
import hashlib
import math
import os
import sys
from fractions import Fraction

sys.set_int_max_str_digits(0)
try:
    from gmpy2 import mpz
except ImportError:
    mpz = int

HERE = os.path.dirname(os.path.abspath(__file__))
SEP = b"\n--RAW--\n"


def field(blob, key):
    for line in blob.decode("utf-8", "replace").splitlines():
        if line.startswith(key + "="):
            return line[len(key) + 1:]


def xor_layer(data, seed):
    ks = hashlib.shake_256(str(seed).encode()).digest(len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


def peel(data, seed):
    head, _, rest = xor_layer(data, seed).partition(SEP)
    return head, rest


def primes_upto(hi):
    s = bytearray([1]) * (hi + 1)
    s[0:2] = b"\x00\x00"
    for i in range(2, int(hi ** .5) + 1):
        if s[i]:
            s[i * i::i] = bytes(len(s[i * i::i]))
    return [i for i in range(2, hi + 1) if s[i]]


# ---------------------------------------------------------------- L1 偏置费马 + 时间锁
def lehman(n, maxk=30, maxsteps=500000):
    for k in range(1, maxk + 1):
        kn = k * n
        a = math.isqrt(kn) + 1
        for _ in range(maxsteps):
            b2 = a * a - kn
            r = math.isqrt(b2)
            if r * r == b2:
                g = math.gcd(a - r, n)
                if 1 < g < n:
                    return g
            a += 1


def layer1(pub):
    n, T, lock = int(field(pub, "n")), int(field(pub, "T")), int(field(pub, "lock"))
    p = lehman(n)
    q = n // p
    phi = (p - 1) * (q - 1)
    y = pow(lock, pow(2, T, phi), n)          # 原版为 pow(2, pow(2, T, phi), n)
    return (lock - y) % n, f"n 分解为 {p.bit_length()} + {q.bit_length()} 位，q/p = {q / p:.6f}"


# ---------------------------------------------------------------- L2 扩展 Wiener
def layer2(h):
    n, e, c = int(field(h, "n")), int(field(h, "e")), int(field(h, "c"))
    cv, hh, kk, a, b = [], (0, 1), (1, 0), e, n
    while b:
        t = a // b
        a, b = b, a - t * b
        hh, kk = (hh[1], t * hh[1] + hh[0]), (kk[1], t * kk[1] + kk[0])
        cv.append((hh[1], kk[1]))

    def check(k, d):
        if k <= 0 or d <= 0 or (e * d - 1) % k:
            return None
        s = n + 1 - (e * d - 1) // k
        if s <= 0 or s % 2:
            return None
        disc = s * s - 4 * n
        r = math.isqrt(disc) if disc >= 0 else -1
        if r < 0 or r * r != disc or ((s - r) // 2) * ((s + r) // 2) != n:
            return None
        return pow(c, d, n)

    for i in range(len(cv) - 1):
        (h1, k1), (h2, k2) = cv[i], cv[i + 1]
        for r in range(60):
            for s in range(60):
                m = check(r * h2 + s * h1, r * k2 + s * k1)
                if m is not None:
                    return m, f"n {n.bit_length()} 位，e {e.bit_length()} 位；由连分数邻项组合求得 d"


# ---------------------------------------------------------------- L3 Williams p+1
def williams(n, B=5_000_000):
    N = mpz(n)

    def lucas_v(P0, m):
        v0, v1 = mpz(2), mpz(P0)
        for bit in bin(m)[2:]:
            if bit == "0":
                v1, v0 = (v0 * v1 - P0) % N, (v0 * v0 - 2) % N
            else:
                v0, v1 = (v0 * v1 - P0) % N, (v1 * v1 - 2) % N
        return v0

    pr = primes_upto(B)
    for P0 in (3, 5, 7, 9, 11, 13):
        v = mpz(P0)
        for i, q in enumerate(pr):
            qp = q
            while qp * q <= B:
                qp *= q
            v = lucas_v(v, qp)
            if i % 500 == 0 or i == len(pr) - 1:
                g = math.gcd(int(v) - 2, n)
                if 1 < g < n:
                    return g, P0
                if g == n:
                    break
    return None, None


def layer3(h):
    n, e, c = int(field(h, "n")), int(field(h, "e")), int(field(h, "c"))
    p, P0 = williams(n)
    q = n // p
    d = pow(e, -1, (p - 1) * (q - 1))
    return pow(c, d, n), f"n {n.bit_length()} 位；Lucas 起始值 P = {P0}"


# ---------------------------------------------------------------- L4 Pohlig–Hellman
def factor_small(m):
    f, d = {}, 2
    while d * d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1
            m //= d
        d += 1
    if m > 1:
        f[m] = f.get(m, 0) + 1
    return f


def bsgs(g, h, P, order):
    m = math.isqrt(order) + 1
    table, e = {}, 1
    for j in range(m):
        table.setdefault(e, j)
        e = e * g % P
    gm, cur = pow(pow(g, m, P), P - 2, P), h
    for i in range(m):
        if cur in table:
            return i * m + table[cur]
        cur = cur * gm % P


def layer4(h):
    P, g, y = int(field(h, "P")), int(field(h, "g")), int(field(h, "h"))
    fac = factor_small(P - 1)
    res, mods = [], []
    for q, ex in fac.items():
        qe = q ** ex
        gi, hi, x = pow(g, (P - 1) // qe, P), pow(y, (P - 1) // qe, P), 0
        for k in range(ex):
            base = pow(gi, q ** (ex - 1), P)
            tgt = pow(pow(gi, -x % (P - 1), P) * hi % P, q ** (ex - 1 - k), P)
            x += bsgs(base, tgt, P, q) * q ** k
        res.append(x % qe)
        mods.append(qe)
    x, M = 0, 1
    for r, m in zip(res, mods):
        x += M * (((r - x) * pow(M, -1, m)) % m)
        M *= m
    return x % (P - 1), f"P {P.bit_length()} 位，P−1 最大素因子 {max(fac).bit_length()} 位"


# ---------------------------------------------------------------- L5 Smart 异常曲线
def ec_add(P1, P2, a, mod):
    if P1 is None:
        return P2
    if P2 is None:
        return P1
    (x1, y1), (x2, y2) = P1, P2
    if x1 == x2 and (y1 + y2) % mod == 0:
        return None
    if P1 == P2:
        lam = (3 * x1 * x1 + a) * pow(2 * y1, -1, mod) % mod
    else:
        lam = (y2 - y1) * pow((x2 - x1) % mod, -1, mod) % mod
    x3 = (lam * lam - x1 - x2) % mod
    return x3, (lam * (x1 - x3) - y1) % mod


def ec_mul(k, P1, a, mod):
    R = None
    while k:
        if k & 1:
            R = ec_add(R, P1, a, mod)
        P1 = ec_add(P1, P1, a, mod)
        k >>= 1
    return R


def layer5(h):
    p = int(field(h, "p"))
    G = (int(field(h, "Gx")), int(field(h, "Gy")))
    Q = (int(field(h, "Qx")), int(field(h, "Qy")))
    p2 = p * p
    (x1, y1), (x2, y2) = G, Q
    a2 = ((y1 * y1 - y2 * y2) - (x1 ** 3 - x2 ** 3)) % p2 * pow((x1 - x2) % p2, -1, p2) % p2

    def plog(Pt):
        rx, ry = ec_mul(p - 1, Pt, a2, p2)
        return ((rx - Pt[0]) // p) * pow((ry - Pt[1]) % p, -1, p) % p

    return plog(Q) * pow(plog(G), -1, p) % p, f"p {p.bit_length()} 位；#E = p，提升到 Z/p² 后取 p 进对数"


# ---------------------------------------------------------------- L6 Coppersmith（e = 3，已知高位）
def lll(B, delta=Fraction(3, 4)):
    B = [r[:] for r in B]
    n = len(B)

    def dot(u, v):
        return sum(x * y for x, y in zip(u, v))

    def gso():
        Bs, mu = [], [[Fraction(0)] * n for _ in range(n)]
        for i in range(n):
            v = [Fraction(x) for x in B[i]]
            for j in range(i):
                mu[i][j] = Fraction(dot(B[i], Bs[j]), dot(Bs[j], Bs[j]))
                v = [v[t] - mu[i][j] * Bs[j][t] for t in range(n)]
            Bs.append(v)
        return Bs, mu

    Bs, mu = gso()
    k = 1
    while k < n:
        for j in range(k - 1, -1, -1):
            if abs(mu[k][j]) > Fraction(1, 2):
                r = (2 * mu[k][j].numerator + mu[k][j].denominator) // (2 * mu[k][j].denominator)
                B[k] = [B[k][t] - r * B[j][t] for t in range(n)]
                Bs, mu = gso()
        if dot(Bs[k], Bs[k]) >= (delta - mu[k][k - 1] ** 2) * dot(Bs[k - 1], Bs[k - 1]):
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            Bs, mu = gso()
            k = max(k - 1, 1)
    return B


def layer6(h):
    n, c, M0 = int(field(h, "n")), int(field(h, "c")), int(field(h, "prefix"))
    X = 1 << int(field(h, "xbits"))
    a2, a1, a0 = 3 * M0 % n, 3 * M0 * M0 % n, (pow(M0, 3, n) - c) % n
    R = lll([[n, 0, 0, 0], [0, n * X, 0, 0], [0, 0, n * X * X, 0], [a0, a1 * X, a2 * X * X, X ** 3]])
    c0, c1, c2, c3 = R[0][0], R[0][1] // X, R[0][2] // (X * X), R[0][3] // X ** 3

    def f(x):
        return ((c3 * x + c2) * x + c1) * x + c0

    cuts = [0, X]
    if c3:
        D = 4 * c2 * c2 - 12 * c3 * c1
        if D >= 0:
            s = math.isqrt(D)
            for sg in (-1, 1):
                t = (-2 * c2 + sg * s) // (6 * c3)
                cuts += [x for x in (t - 1, t, t + 1) if 0 <= x <= X]
    cuts = sorted(set(cuts))
    for lo, hi in zip(cuts, cuts[1:]):
        flo, fhi = f(lo), f(hi)
        if flo == 0:
            return M0 + lo, ""
        if fhi == 0:
            return M0 + hi, ""
        if (flo < 0) != (fhi < 0):
            l, r, inc = lo, hi, fhi > flo
            while l <= r:
                m = (l + r) // 2
                fm = f(m)
                if fm == 0:
                    return M0 + m, f"n {n.bit_length()} 位，未知低位 {X.bit_length() - 1} 位；4 维格 LLL"
                l, r = (m + 1, r) if (fm < 0) == inc else (l, m - 1)


# ---------------------------------------------------------------- L7 LWE / HNP（Kannan 嵌入）
def layer7(h):
    q, Berr = int(field(h, "q")), int(field(h, "Berr"))
    A = [int(x) for x in field(h, "A").split(",")]
    b = [int(x) for x in field(h, "b").split(",")]
    m = len(A)
    inv0 = pow(A[0], -1, q)
    t = [A[i] * inv0 % q for i in range(m)]
    u = [(b[i] - t[i] * b[0]) % q for i in range(m)]
    dim = m + 1
    M = [[0] * dim for _ in range(dim)]
    for i in range(1, m):
        M[i - 1][i] = q
    M[m - 1] = [1] + t[1:] + [0]
    M[m] = [0] + u[1:] + [Berr]
    for row in lll(M):
        if abs(row[-1]) == Berr:
            e0 = row[0] if row[-1] == Berr else -row[0]
            return (b[0] - e0) * inv0 % q, f"{m} 个样本，q {q.bit_length()} 位，误差界 {Berr.bit_length()} 位"


LAYERS = [("L2 扩展 Wiener", layer2), ("L3 Williams p+1", layer3), ("L4 Pohlig–Hellman", layer4),
          ("L5 Smart 异常曲线", layer5), ("L6 Coppersmith", layer6), ("L7 LWE / Kannan 嵌入", layer7)]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "grandmaster_reply.txt")
    pub = open(path, "rb").read()
    seed, note = layer1(pub)
    print(f"[L1 偏置费马 + 时间锁] {note}")
    head, rest = peel(base64.b64decode(field(pub, "blob")), seed)
    for name, solve in LAYERS:
        assert head.startswith(b"[L"), f"{name} 之前的解密失败"
        seed, note = solve(head)
        print(f"[{name}] {note}")
        head, rest = peel(rest, seed)
    msg = head + (SEP + rest if rest else b"")
    ok = hashlib.sha256(msg).hexdigest() == field(pub, "commitment")
    print(f"\n明文 SHA-256 与 commitment 一致：{ok}")
    print("\n明文：\n  " + msg.decode("utf-8"))
    assert ok


if __name__ == "__main__":
    main()

from migen import *
from itertools import starmap


def bulk_assign(siglist, *signals):
    return [a.eq(b) for a, b in zip(siglist, signals)]


class HalfMultiplyAdd(Module):
    def __init__(self):
        self.a = Signal((16, True))
        self.b = Signal((16, True))
        self.c = Signal((16, True))
        self.p = Signal((16, True))
        self.xx = xx = Signal(32)
        self.comb += xx.eq(self.a * self.b)
        self.comb += self.p.eq(xx[16:] + self.c)
        self.inputs = (self.a, self.b, self.c)
        self.outputs = (self.p,)


class ISin(Module):
    def __init__(self):
        self.x = x = Signal((16, True))
        self.s = s = Signal((16, True))

        y = Signal((16, True))
        cc = Signal((16, True))

        n = Signal(3)
        self.comb += n.eq(x[13:16] + Constant(1, 3))
        y = Cat(Constant(0, 2), x[:14])
        
        h0 = HalfMultiplyAdd()
        hc = HalfMultiplyAdd()
        hs = HalfMultiplyAdd()
        h2 = HalfMultiplyAdd()
        self.submodules += [h0, hc, hs, h2]

        z = h0.p
        sumc = hc.p
        sums = hs.p
        sum1 = h2.p

        self.comb += bulk_assign(h0.inputs, y, y, Constant(0))
        self.comb += bulk_assign(hc.inputs, z, Constant(0x0fbd, (16, True)), Constant(-0x4ee9, (16, True)))
        self.comb += bulk_assign(hs.inputs, z, Constant(0x04f8, (16, True)), Constant(-0x2953, (16, True)))
        self.comb += bulk_assign(h2.inputs, z, sums, Constant(0x6487, (16, True)))

        t0 = Signal((16, True))
        t1 = Signal((16, True))
        sa = Signal((16, True))

        self.comb += [
            If(n[1], # cosine
                t0.eq(z),
                t1.eq(sumc),
                sa.eq(cc + Constant(0x7fff, (16, True)))
            ).Else( # sine
                t0.eq(y),
                t1.eq(sum1),
                sa.eq(cc)
            )
        ]

        cc32 = Signal(32)
        self.comb += [
            cc32.eq(t0 * t1),
            cc.eq(cc32[15:31]),
            If(n[2], s.eq(-sa)).Else(s.eq(sa))
        ]


class ICos(Module):
    def __init__(self):
        self.x = Signal((16, True))
        self.s = Signal((16, True))

        isin = ISin()
        self.submodules += isin
        self.comb += isin.x.eq(self.x + Constant(0x4000))
        self.comb += self.s.eq(isin.s)


class ISinCosTest(Module):
    def __init__(self):
        self.isin, self.icos = ISin(), ICos()
        self.submodules += [self.isin, self.icos]


def testbench(dut):
    for i in range(65536):
        yield dut.isin.x.eq(Constant(i, (16, True)))
        yield dut.icos.x.eq(Constant(i, (16, True)))
        print("{} {}".format((yield dut.isin.s), (yield dut.icos.s)))
        yield

dut = ISinCosTest()
run_simulation(dut, testbench(dut), vcd_name="isin.vcd")

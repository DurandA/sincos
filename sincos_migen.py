from migen import *


class HalfMultiplyAdd(Module):
    def __init__(self, a, b, c, p):
        self.xx = xx = Signal(32)
        self.comb += xx.eq(a * b)
        self.comb += p.eq(xx[16:] + c)


class ISin(Module):
    def __init__(self, x, s):
        y = Signal((16, True))
        cc = Signal((16, True))

        n = Signal(3)
        self.comb += n.eq(x[13:16] + Constant(1, 3))
        y = Cat(Constant(0, 2), x[:14])

        z = Signal((16, True))
        sumc = Signal((16, True))
        sums = Signal((16, True))
        sum1 = Signal((16, True))

        h0 = HalfMultiplyAdd(y, y, Constant(0), z)
        hc = HalfMultiplyAdd(z, Constant(0x0fbd, (16, True)), Constant(-0x4ee9, (16, True)), sumc)
        hs = HalfMultiplyAdd(z, Constant(0x04f8, (16, True)), Constant(-0x2953, (16, True)), sums)
        h2 = HalfMultiplyAdd(z, sums, Constant(0x6487, (16, True)), sum1)
        self.submodules += [h0, hc, hs, h2]

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
    def __init__(self, x, s):
        isin = ISin(x + Constant(0x4000), s)
        self.submodules += isin


class ISinCosTest(Module):
    def __init__(self):
        self.x = Signal((16, True))
        self.iss = Signal((16, True))
        self.ics = Signal((16, True))
        self.isin, self.icos = ISin(self.x, self.iss), ICos(self.x, self.ics)
        self.submodules += [self.isin, self.icos]


def testbench(dut):
    for i in range(65536):
        yield dut.x.eq(Constant(i, (16, True)))
        print("{} {}".format((yield dut.iss), (yield dut.ics)))
        yield

if __name__ == "__main__":
    dut = ISinCosTest()
    run_simulation(dut, testbench(dut), vcd_name="isin.vcd")

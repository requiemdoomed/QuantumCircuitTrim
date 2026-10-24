import itertools
import math
import random
import unittest
from circuittrim import Circuit, Gate, evolve, parse_circuit, probabilities, simplify, statevector, verify
from circuittrim.core import ARITY, INVERSE


class ParsingTests(unittest.TestCase):
    def test_lowercase_semicolons_comments_and_roundtrip(self):
        c = parse_circuit('h q0; cx 0, 1 # ignored; X 9\n\n t 1',2)
        self.assertEqual(c.to_text(),'H 0\nCX 0 1\nT 1')
        self.assertEqual(parse_circuit(c.to_text(),2),c)

    def test_empty_input(self):
        self.assertEqual(parse_circuit('# nothing\n',3),Circuit(3))

    def test_errors_show_line_numbers(self):
        for bad in ['BAD 1','CX 0 0','X -1','H 2','H potato','H 0 1']:
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError,'Line 2'):
                parse_circuit('H 0\n'+bad,2)

    def test_invalid_values(self):
        for n in [0,5,True,1.5,'2']:
            with self.subTest(n=n), self.assertRaises(ValueError): Circuit(n)
        for args in [('X',(-1,)),('X',(True,)),('CX',(0,0)),('X',None),(1,(0,))]:
            with self.subTest(args=args), self.assertRaises(ValueError): Gate(*args)
        for gates in [[Gate('X',(1,))],['X'],None]:
            with self.subTest(gates=gates), self.assertRaises(ValueError): Circuit(1,gates)
        with self.assertRaises(ValueError): parse_circuit(None)

    def test_limits(self):
        self.assertEqual(len(parse_circuit('X 0\n'*120,1).gates),120)
        with self.assertRaises(ValueError): parse_circuit('X 0\n'*121,1)
        with self.assertRaises(ValueError): parse_circuit(' '*16001)

    def test_symmetric_gates_and_cx_direction(self):
        for name in ['SWAP','CZ']:
            self.assertEqual(Gate(name,(1,0)),Gate(name,(0,1)))
        self.assertNotEqual(Gate('CX',(1,0)),Gate('CX',(0,1)))


class SimulationTests(unittest.TestCase):
    def assertState(self,actual,expected):
        self.assertEqual(len(actual),len(expected))
        for a,b in zip(actual,expected): self.assertLess(abs(a-b),1e-12)

    def test_identity_on_all_basis_inputs(self):
        for n in range(1,5):
            for basis in range(2**n):
                self.assertState(statevector(Circuit(n),basis),[int(i==basis) for i in range(2**n)])

    def test_known_single_qubit_matrices(self):
        r=1/math.sqrt(2)
        expected={'H':((r,r),(r,-r)),'X':((0,1),(1,0)),'Y':((0,1j),(-1j,0)),
                  'Z':((1,0),(0,-1)),'S':((1,0),(0,1j)),'SDG':((1,0),(0,-1j)),
                  'T':((1,0),(0,complex(r,r))),'TDG':((1,0),(0,complex(r,-r)))}
        for name,columns in expected.items():
            for basis,column in enumerate(columns):
                with self.subTest(name=name,basis=basis):
                    self.assertState(statevector(parse_circuit(name+' 0',1),basis),column)

    def test_q0_is_lowest_bit(self):
        self.assertEqual(probabilities(parse_circuit('X 0',3))['001'],1)
        self.assertEqual(probabilities(parse_circuit('X 2',3))['100'],1)

    def test_two_qubit_truth_tables(self):
        for text,outputs in [('CX 0 1',[0,3,2,1]),('CX 1 0',[0,1,3,2]),('SWAP 0 1',[0,2,1,3])]:
            for basis,out in enumerate(outputs):
                self.assertEqual(statevector(parse_circuit(text,2),basis)[out],1)
        for basis in range(4):
            self.assertEqual(statevector(parse_circuit('CZ 0 1',2),basis)[basis],-1 if basis==3 else 1)

    def test_bell_and_ghz_states(self):
        r=1/math.sqrt(2)
        self.assertState(statevector(parse_circuit('H 0; CX 0 1',2)),(r,0,0,r))
        p=probabilities(parse_circuit('H 0; CX 0 1; CX 1 2',3))
        self.assertAlmostEqual(p['000'],0.5)
        self.assertAlmostEqual(p['111'],0.5)
        self.assertAlmostEqual(sum(p.values()),1)

    def test_complex_state(self):
        state=(1/math.sqrt(2),1j/math.sqrt(2))
        self.assertState(evolve(parse_circuit('H 0; T 0; TDG 0; H 0',1),state),state)

    def test_invalid_states(self):
        for state in [(0,0),(1,),(1,float('nan')),(1,float('inf')),('bad',0),None]:
            with self.subTest(state=state),self.assertRaises(ValueError): evolve(Circuit(1),state)
        for basis in [-1,2,True,0.0]:
            with self.subTest(basis=basis),self.assertRaises(ValueError): statevector(Circuit(1),basis)

    def test_probability_matching_is_not_operator_equality(self):
        z,identity=parse_circuit('Z 0',1),Circuit(1)
        self.assertEqual(probabilities(z),probabilities(identity))
        self.assertFalse(verify(z,identity).equivalent)

    def test_global_phase_is_compared_strictly(self):
        self.assertFalse(verify(parse_circuit('X 0; Z 0; X 0; Z 0',1),Circuit(1)).equivalent)

    def test_verification_validation(self):
        with self.assertRaises(ValueError): verify(Circuit(1),Circuit(2))
        for tolerance in [0,-1,float('nan'),float('inf'),'bad',True]:
            with self.subTest(tolerance=tolerance),self.assertRaises(ValueError):
                verify(Circuit(1),Circuit(1),tolerance)

    def test_every_gate_against_independent_dense_reference(self):
        r=1/math.sqrt(2)
        single={'H':[[r,r],[r,-r]],'X':[[0,1],[1,0]],'Y':[[0,-1j],[1j,0]],
                'Z':[[1,0],[0,-1]],'S':[[1,0],[0,1j]],'SDG':[[1,0],[0,-1j]],
                'T':[[1,0],[0,complex(r,r)]],'TDG':[[1,0],[0,complex(r,-r)]]}
        rng=random.Random(85)
        for n in range(1,5):
            raw=[complex(rng.random(),rng.random()) for _ in range(2**n)]
            norm=math.sqrt(sum(abs(x)**2 for x in raw))
            state=[x/norm for x in raw]
            for name,arity in ARITY.items():
                for wires in itertools.permutations(range(n),arity):
                    expected=[0j]*len(state)
                    for source,amplitude in enumerate(state):
                        bits=list(format(source,f'0{n}b'))[::-1]
                        if arity==1:
                            q=wires[0]
                            old=int(bits[q])
                            for new in (0,1):
                                out=bits.copy()
                                out[q]=str(new)
                                expected[int(''.join(out[::-1]),2)]+=single[name][new][old]*amplitude
                        else:
                            a,b=wires
                            phase=1
                            if name=='CX' and bits[a]=='1': bits[b]='0' if bits[b]=='1' else '1'
                            elif name=='CZ' and bits[a]==bits[b]=='1': phase=-1
                            elif name=='SWAP': bits[a],bits[b]=bits[b],bits[a]
                            expected[int(''.join(bits[::-1]),2)]+=phase*amplitude
                    with self.subTest(n=n,name=name,wires=wires):
                        self.assertState(evolve(Circuit(n,(Gate(name,wires),)),state),expected)


class SimplificationTests(unittest.TestCase):
    def test_all_inverse_pairs_on_all_wires(self):
        for n in range(1,5):
            for name,arity in ARITY.items():
                for wires in itertools.permutations(range(n),arity):
                    c=Circuit(n,(Gate(name,wires),Gate(INVERSE[name],wires)))
                    result=simplify(c)
                    with self.subTest(n=n,name=name,wires=wires):
                        self.assertEqual(result.simplified,Circuit(n))
                        self.assertTrue(verify(c,result.simplified).equivalent)

    def test_cascade_and_original_indices(self):
        result=simplify(parse_circuit('H 0; X 0; X 0; H 0',1))
        self.assertEqual(result.removed,4)
        self.assertEqual(result.reduction_percent,100)
        self.assertEqual([(x.left_index,x.right_index) for x in result.cancellations],[(1,2),(0,3)])

    def test_nonadjacent_different_wires_and_noninverse_gates_stay(self):
        for text in ['X 0; H 1; X 0','X 0; X 1','CX 0 1; CX 1 0','S 0; S 0; T 0; T 0']:
            c=parse_circuit(text,2)
            self.assertEqual(simplify(c).simplified,c)

    def test_empty_statistics(self):
        result=simplify(Circuit(2))
        self.assertEqual(result.removed,0)
        self.assertEqual(result.reduction_percent,0)
        self.assertEqual(result.cancellations,())

    def test_bell_example(self):
        from circuittrim.presets import PRESETS
        n,text=PRESETS['Bell state · 12 gates to 2']
        result=simplify(parse_circuit(text,n))
        self.assertEqual(len(result.original.gates),12)
        self.assertEqual(result.simplified.to_text(),'H 0\nCX 0 1')
        self.assertTrue(verify(result.original,result.simplified).equivalent)

    def test_500_randomized_circuits(self):
        rng=random.Random(2026)
        for case in range(500):
            n=rng.randrange(1,5)
            available=[name for name,arity in ARITY.items() if arity<=n]
            gates=[]
            for _ in range(rng.randrange(1,35)):
                name=rng.choice(available)
                gate=Gate(name,tuple(rng.sample(range(n),ARITY[name])))
                gates.append(gate)
                if rng.random()<0.4: gates.append(Gate(INVERSE[name],gate.qubits))
            c=Circuit(n,tuple(gates))
            result=simplify(c)
            with self.subTest(case=case):
                self.assertTrue(verify(c,result.simplified).equivalent)
                self.assertEqual(simplify(result.simplified).simplified,result.simplified)
                self.assertEqual(result.removed,2*len(result.cancellations))
                self.assertAlmostEqual(sum(probabilities(c).values()),1)


if __name__=='__main__':
    unittest.main()

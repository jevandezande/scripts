import unittest
from sys import path
path.insert(0, '..')
from qgrep.basis import BasisFunction, Basis, BasisSet
import numpy as np
from collections import OrderedDict
import os


class TestBasisFunction(unittest.TestCase):
    """Tests a BasisFunction"""
    def setUp(self):
        self.bfs = BasisFunction('S', [1, 2], [0.5, 0.5])
        self.bfp = BasisFunction('P', [0.01, 0.2, 1], [0.3, 0.4, 0.3])
        self.bfd = BasisFunction('D', [1, 2], [0.3, 0.7], [0.4, 0.6])
        self.bfsp = BasisFunction('SP', [0.1, 0.4, 3], [0.2, 0.3, 0.5], [0.1, 0.3, 0.6])

    def test_len(self):
        """Test __len__"""
        self.assertEqual(2, len(self.bfs))
        self.assertEqual(3, len(self.bfp))
        self.assertEqual(2, len(self.bfd))
        self.assertEqual(3, len(self.bfsp))

    def test_getseteq(self):
        """Test __getitem__ and __setitem__"""
        # Convert np.array to list to prevent error in case.py as the truth value of an array is ambiguous
        self.assertEqual([1.0, 0.5], list(self.bfs[0]))
        # Convert to a list of lists
        self.assertEqual([[0.01, 0.3], [1.0, 0.3]], list(map(list, self.bfp[::2])))

        self.bfs[0] = [1, 2]
        self.assertEqual([1.0, 2], list(self.bfs[0]))
        self.assertRaises(ValueError, self.bfs.__setitem__, 1, [1, 2, 4])
        self.bfd[0] = [1, 0.2, 0.3]
        self.assertEqual([1.0, 0.2, 0.3], list(self.bfd[0]))
        self.bfsp[0] = [1, 2, 4]
        self.assertEqual([1, 2, 4], list(self.bfsp[0]))
        self.assertRaises(ValueError, self.bfsp.__setitem__, 1, [1, 2])

        self.assertEqual(self.bfs, self.bfs)

    def test_check_exps(self):
        """Test check_exps"""
        BasisFunction.check_exps([1, 2])
        self.assertRaises(ValueError, BasisFunction.check_exps, [1, 2, -3])

    def test_exps_coeffs_coeffs2(self):
        """Test exps, coeffs, and coeffs2"""
        self.assertEqual([1, 2], list(self.bfs.exps))
        self.assertEqual([0.3, 0.4, 0.3], list(self.bfp.coeffs))
        self.assertEqual([0.4, 0.6], list(self.bfd.coeffs2))

    def test_reprprint(self):
        """Test print"""
        s_gamess = '''S     2
  1         1.0000000   0.5000000
  2         2.0000000   0.5000000
'''
        p_gaussian94 = '''P     3
        0.0100000   0.3000000
        0.2000000   0.4000000
        1.0000000   0.3000000
'''
        sp_gaussian94 = '''SP    3
        0.1000000   0.2000000   0.1000000
        0.4000000   0.3000000   0.3000000
        3.0000000   0.5000000   0.6000000
'''
        self.assertEqual('<BasisFunction S 2>', repr(self.bfs))
        self.assertEqual('<BasisFunction P 3>', repr(self.bfp))
        self.assertEqual('<BasisFunction SP 3x2>', repr(self.bfsp))
        self.assertEqual(s_gamess, self.bfs.print('gamess'))
        self.assertEqual(p_gaussian94, self.bfp.print())
        #print(self.bfsp.print())
        self.assertEqual(sp_gaussian94, self.bfsp.print())

    def test_decontracted(self):
        """Tests decontraction of basis function"""
        bf1 = BasisFunction('S', [1], [1])
        bf2 = BasisFunction('S', [2], [1])
        decon1 = list(self.bfs.decontracted())
        self.assertEqual(decon1[0], bf1)
        self.assertEqual(decon1[1], bf2)

        bfs1 = BasisFunction('S', [0.1], [1])
        bfs2 = BasisFunction('S', [0.4], [1])
        bfs3 = BasisFunction('S', [3  ], [1])
        bfp1 = BasisFunction('P', [0.1], [1])
        bfp2 = BasisFunction('P', [0.4], [1])
        bfp3 = BasisFunction('P', [3  ], [1])
        decon2 = list(self.bfsp.decontracted())
        self.assertEqual(decon2[0], bfs1)
        self.assertEqual(decon2[1], bfs2)
        self.assertEqual(decon2[2], bfs3)
        self.assertEqual(decon2[3], bfp1)
        self.assertEqual(decon2[4], bfp2)
        self.assertEqual(decon2[5], bfp3)


class TestBasis(unittest.TestCase):
    """Tests a basis, which contains BasisFunctions"""
    def setUp(self):
        self.bfs = BasisFunction('S', [1, 2], [0.5, 0.5])
        self.bfp = BasisFunction('P', [0.01, 0.2, 1], [0.3, 0.4, 0.3])
        self.bfsp = BasisFunction('SP', [0.1, 0.4, 3], [0.2, 0.3, 0.5], [0.1, 0.3, 0.6])
        self.basis = Basis('C', [self.bfs, self.bfp, self.bfsp])

    def test_lengetsetdeleq(self):
        """Test __len__, __getitem__ and __setitem__, __delitem__, __eq__"""
        self.assertEqual(3, len(self.basis))
        bf = BasisFunction('F', [4, 9], [0.1, 0.9])
        self.basis[0] = bf
        self.assertEqual(bf, self.basis[0])
        self.assertRaises(SyntaxError, self.basis.__setitem__, 0, 1)
        del self.basis[2]
        self.assertRaises(IndexError, self.basis.__getitem__, 2)
        basis = Basis('C', [self.bfsp])
        basis2 = Basis('C', [self.bfsp])
        self.assertEqual(basis, basis2)

    def test_reprstrprint(self):
        """Test print"""
        c_gamess = '''C
S     2
  1         1.0000000   0.5000000
  2         2.0000000   0.5000000
P     3
  1         0.0100000   0.3000000
  2         0.2000000   0.4000000
  3         1.0000000   0.3000000
SP    3
  1         0.1000000   0.2000000   0.1000000
  2         0.4000000   0.3000000   0.3000000
  3         3.0000000   0.5000000   0.6000000
'''
        c_gaussian94 = '''C    0
S     2
        1.0000000   0.5000000
        2.0000000   0.5000000
P     3
        0.0100000   0.3000000
        0.2000000   0.4000000
        1.0000000   0.3000000
SP    3
        0.1000000   0.2000000   0.1000000
        0.4000000   0.3000000   0.3000000
        3.0000000   0.5000000   0.6000000
'''
        self.assertEqual('<Basis C 3>', repr(self.basis))
        self.assertEqual(c_gaussian94, str(self.basis))
        self.assertEqual(c_gamess, self.basis.print('gamess'))


class TestBasisSet(unittest.TestCase):
    """Test the BasisSet class"""
    def setUp(self):
        bfs = BasisFunction('S', [1, 2], [0.5, 0.5])
        bfp = BasisFunction('P', [0.01, 0.2, 1], [0.3, 0.4, 0.3])
        self.h = Basis('H', [bfs, bfp])
        bfs = BasisFunction('S', [0.1, 0.4], [0.6, 0.4])
        bfsp = BasisFunction('SP', [0.1, 0.4, 3], [0.2, 0.3, 0.5], [0.1, 0.3, 0.6])
        self.c = Basis('C', [bfs, bfsp])

        atoms = OrderedDict([('H', self.h), ('C', self.c)])
        self.basis_set = BasisSet(atoms)

    def test_getsetdeleq(self):
        """Test __getitem__, __setitem__, __delitem__, and __eq__"""
        bfs = BasisFunction('S', [0.2, 0.4], [0.3, 0.7])
        b = Basis('B', [bfs])
        self.basis_set['B'] = b
        self.assertEqual(self.c, self.basis_set['C'])
        self.assertEqual(b, self.basis_set['B'])
        del self.basis_set['B']
        self.assertRaises(KeyError, self.basis_set.__getitem__, 'B')
        bfs = BasisFunction('S', [1, 2], [0.5, 0.5])
        bfp = BasisFunction('P', [0.01, 0.2, 1], [0.3, 0.4, 0.3])
        h = Basis('H', [bfs, bfp])
        bfs = BasisFunction('S', [0.1, 0.4], [0.6, 0.4])
        bfsp = BasisFunction('SP', [0.1, 0.4, 3], [0.2, 0.3, 0.5], [0.1, 0.3, 0.6])
        c = Basis('C', [bfs, bfsp])
        atoms = OrderedDict([('H', h), ('C', c)])
        basis_set2 = BasisSet(atoms)
        self.assertEqual(basis_set2, self.basis_set)

    def test_iter(self):
        bs_it = iter(self.basis_set)
        self.assertEqual(self.h, next(bs_it))
        self.assertEqual(self.c, next(bs_it))

    def test_check_basis_set(self):
        """Test check_basis_set"""
        self.assertRaises(SyntaxError, BasisSet.check_basis_set, ({'H': 1}))
        self.assertRaises(SyntaxError, BasisSet.check_basis_set, (OrderedDict([('H', 1)])))

    def test_change_basis_set(self):
        """Test change_basis_set"""
        atoms = OrderedDict([('C', Basis('C', [BasisFunction('S', [1], [1])]))])
        self.basis_set.change_basis_set(atoms)
        bad_bs = OrderedDict([('H', 1)])
        self.assertRaises(SyntaxError, self.basis_set.change_basis_set, (bad_bs,))

    def test_reprreadprint(self):
        """Test read and print"""
        test_file = 'my_basis.gbs.tmp'
        test_file_bagel = 'my_basis.json.tmp'
        with open(test_file, 'w') as f:
            f.write(self.basis_set.print('gaussian94'))
        bs1 = BasisSet.read(test_file, 'gaussian94')
        self.assertEqual('<BasisSet my_basis>', repr(bs1))
        with open(test_file, 'w') as f:
            f.write(bs1.print('gamess'))
        with open(test_file_bagel, 'w') as f:
            f.write(bs1.print('bagel'))
        bs2 = BasisSet.read(test_file, 'gamess')

        self.assertEqual(bs1, bs2)
        os.remove(test_file)
        os.remove(test_file_bagel)
        self.assertRaises(SyntaxError, bs2.print, 'turbomole')

    def test_values(self):
        """Test values"""
        vals = [[np.array([[1.0, 0.5], [2.0, 0.5]]),
                 np.array([[0.01, 0.3], [0.2, 0.4], [1.0, 0.3]])],
                [np.array([[0.1, 0.6], [0.4, 0.4]]),
                 np.array([[0.1, 0.2], [0.4, 0.3], [3.0, 0.5]])]]
        self.assertEqual(vals[0][0][0][1], self.basis_set.values()[0][0][0][1])
        self.assertEqual(vals[0][1][1][0], self.basis_set.values()[0][1][1][0])


if __name__ == '__main__':
    unittest.main()

from collections import OrderedDict
from helper import convert_name, atomic_number
import numpy as np


class Contraction:
    """A contraction of basis functions"""
    def __init__(self, func_type, exps, coeffs, c2=[]):
        func_type = func_type.upper()
        if not func_type in 'SPDFGHIKLMN':
            raise SyntaxError("Invalid angular momentum.")
        self.func_type = func_type

        if len(exps) == 0 or len(exps) != len(coeffs):
            raise SyntaxError('Need coefficients and exponents of the same length, got: \n{}\n{}'.format(exps, coeffs))
        Contraction.check_exps(exps)
        Contraction.check_coeffs(coeffs)
        if len(c2) > 0 and len(c2) != len(coeffs):
            raise SyntaxError('Second set of coefficients must have the same number as the first set')
        self.c2 = True
        if len(c2) == 0:
            self.values = np.array(list(zip(exps, coeffs)))
            self.c2 = False
        else:
            self.values = np.array(list(zip(exps, coeffs, c2)))

    def __len__(self):
        return len(self.values)

    def __getitem__(self, item):
        return self.values[item]

    def __setitem__(self, item, value):
        if len(value) != len(self.values[0]):
            raise ValueError("Incorrect size, expected {} elements.".format(len(self.values[0])))
        self.values[item] = value

    @staticmethod
    def check_exps(exps):
        """Check to make sure that the exponents are valid"""
        for exp in exps:
            if not exp > 0:
                raise SyntaxError("Exponents must be greater than 0.")

    @staticmethod
    def check_coeffs(coeffs):
        """Check to make sure that the coefficients are valid"""
        pass

    @property
    def exps(self):
        return self.values[:, 0]

    @exps.setter
    def exps(self, values):
        Contraction.check_exps(values)
        self.values[:, 0] = values

    @property
    def coeffs(self):
        return self.values[:, 1]

    @coeffs.setter
    def coeffs(self, value):
        self.values[:, 1] = value

    @property
    def coeffs2(self):
        return self.values[:, 2]

    @coeffs2.setter
    def coeffs2(self, value):
        self.values[:, 2] = value

    def print(self, style='gaussian94', atom=''):
        """Print the contraction to a string"""
        out = '{:<2}    {}'.format(self.func_type, len(self))
        if style == 'gaussian94':
            if self.c2:
                out += '\n' + '\n'.join(('{:>17.7f}' + ' {:> 11.7f}'*2).format(*trip) for trip in self.values)
            else:
                out += '\n' + '\n'.join('{:>17.7f} {:> 11.7f}'.format(*pair) for pair in self.values)
        elif style == 'gamess':
            if self.c2:
                for i, trip in enumerate(self.values, start=1):
                    out += ('\n {:>2} {:>14.7f}' + ' {:> 11.7f}'*2).format(i, *trip)
            else:
                for i, pair in enumerate(self.values, start=1):
                    out += '\n {:>2} {:>14.7f} {:> 11.7f}'.format(i, *pair)
        else:
            raise SyntaxError('Only gaussian94 and gamess are currently supported.')
        return out + '\n'


class Basis:
    """A basis for an atom"""
    def __init__(self, atom='', contractions=[]):
        self.atom = atom
        if not isinstance(contractions, list) or not all(map(lambda x: isinstance(x, Contraction), contractions)):
            raise SyntaxError("Expected a list of contractions")
        self.cons = contractions

    def __len__(self):
        """Return the number of contractions"""
        return len(self.cons)

    def __getitem__(self, i):
        """Return the ith contraction"""
        return self.cons[i]

    def __setitem__(self, i, value):
        """Sets the ith contraction"""
        if not isinstance(value, Contraction):
            raise SyntaxError("Expecting a Contraction object, instead got: {}".format(type(value)))
        self.cons[i] = value

    def print(self, style='gaussian94', print_name=True):
        """Print all contractions in the specified format"""
        out = ''
        if style == 'gaussian94':
            if print_name:
                out += '{}    0\n'.format(self.atom)
        elif style == 'gamess':
            if print_name:
                out += '{}\n'.format(convert_name(self.atom).upper(), len(self))
        else:
            raise SyntaxError('Only gaussian94 and gamess currently supported')
        return out + ''.join([c.print(style, self.atom) for c in self.cons])


class BasisSet:
    """A BasisSet, which consists of the basis for multiple atoms"""
    def __init__(self, atoms=OrderedDict):
        """Atoms is a dictionary of atom:Basis"""
        if isinstance(atoms, OrderedDict):
            BasisSet.check_basis_set(atoms)
            self.atoms = atoms
            self.am = 'spherical'
        elif isinstance(atoms, str):
            self.read_basis(atoms)
        else:
            raise SyntaxError("Invalid input basis set")

    @staticmethod
    def check_basis_set(atoms):
        """Check a BasisSet"""
        if isinstance(atoms, OrderedDict):
            for atom, basis in atoms.items():
                # Assume that the Basis was made correctly
                if not isinstance(basis, Basis):
                    raise SyntaxError('Expecting a dictionary of atom:Basis.')
        else:
            raise SyntaxError('Expecting a dictionary (of form atom:Basis).')

    def change_basis_set(self, basis_set):
        """Change to a new basis"""
        BasisSet.check_basis_set(basis_set)
        self.atoms = basis_set

    def read_basis_set(self, in_file="basis.gbs", style='gaussian94'):
        """Read a gaussian94 style basis set"""
        #  assume spherical
        self.am = 'spherical'
        self.atoms = OrderedDict()
        num_skip = 0
        if style == 'gaussian94':
            atom_separator = '****'
        elif style == 'gamess':
            num_skip = 1
            atom_separator = '\n\n'
        else:
            raise NotImplementedError("Only gaussian94 style basis sets are currently supported.")
        basis_set_str = open(in_file).read().strip()
        for chunk in basis_set_str.split(atom_separator):
            if len(chunk) == 0:
                continue
            name, *basis_chunk = chunk.strip().split('\n')
            name = name.split()[0]
            i = 0
            con_list = []
            while i < len(basis_chunk):
                am, num = basis_chunk[i].split()
                num = int(num)
                con = []
                for line in basis_chunk[i+1:i + num + 1]:
                    con.append([float(x) for x in line.split()[num_skip:]])
                # Makes an empty list if no elements for coeffs2
                exps, coeffs, *coeffs2 = zip(*con)
                if coeffs2:
                    # Remove extra list
                    coeffs2 = coeffs2[0]
                con_list.append(Contraction(am, exps, coeffs, coeffs2))
                i += num + 1
            self.atoms[name] = Basis(name, con_list)

    def print_basis_set(self, style='gaussian94'):
        """Print the basis to a string"""
        out = ''
        if style == 'gaussian94':
            separator = '****\n'
            atom_format = '{}    0\n'
            out = separator
        if style == 'gamess':
            separator = '\n'
            atom_format = '{}'
        # Ideally would be sorted according to periodic table
        for atom, basis in self.atoms.items():
            out += basis.print(style) + separator

        return out

    def values(self):
        """Returns a list of list of np.array(exp, coeff, *coeff2)"""
        vals = []
        for name, basis in self.atoms.items():
            atom_vals = []
            for con in basis:
                atom_vals.append(con.values)
                pass
            vals.append(atom_vals)
        return vals

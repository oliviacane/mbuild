from collections import defaultdict
from copy import copy
import os
from warnings import warn
from pkg_resources import resource_filename
import sys

from mbuild.compound import Compound
from mbuild.orderedset import OrderedSet

# Map opls ids to the functions that check for them.
rules = dict()

# Globally maintained neighbor information (see `neighbor_types()`).
neighbor_types_map = {}


def opls_atomtypes(compound):
    """Determine OPLS-aa atomtypes for all atoms in `compound`.

    This is where everything is orchestrated and the outer iteration happens.


    TODO: look into factoring out functions for different rings (see 145)
    """
    # Build a map to all of the supported opls_* functions.
    for fn, fcn in sys.modules[__name__].__dict__.items():
        if fn.startswith('opls_'):
            rules[fn.split("_")[1]] = fcn

    # Add white- and blacklists to all atoms.
    for atom in compound.yield_atoms():
        prepare(atom)

    max_iter = 10
    for iter_cnt in range(max_iter):
        print ("Iteration {}".format(iter_cnt))

        # For comparing the lengths of the white- and blacklists.
        old_len = 0
        new_len = 0
        for atom in compound.yield_atoms():
            old_len += len(atom.opls_whitelist)
            old_len += len(atom.opls_blacklist)

            if atom.kind == 'G':  # Ignore Ports.
                continue
            elif atom.kind == 'C':
                carbon(atom)
            elif atom.kind == 'H':
                hydrogen(atom)
            else:
                warn('Atom kind {} not supported'.format(atom.kind))

            new_len += len(atom.opls_whitelist)
            new_len += len(atom.opls_blacklist)

        # Nothing changed, we're done!
        if old_len == new_len:
            break
    else:
        warn("Reached maximum iterations. Something probably went wrong.")


def prepare(atom):
    """Add white- and blacklists to atom. """
    atom.extras['opls_whitelist'] = OrderedSet()
    atom.extras['opls_blacklist'] = OrderedSet()


def run_rule(atom, rule_id):
    """Execute the rule function for a specified OPLS-aa atomtype. """
    if not rule_id in atom.opls_blacklist and not rule_id in atom.opls_whitelist:
        try:
            rule_fn = rules[rule_id]
        except KeyError:
            raise KeyError('Rule for {} not implemented'.format(rule_id))
        rule_fn(atom)


def neighbor_types(atom):
    """Maintains number of neighbors of each element type for all atoms.

    The dict maintained is `neighbor_types_map` and is organized as follows:
        atom: defaultdict{element: number of neighbors of that element type}

    E.g. for an atom with 3 carbon and 1 hydrogen neighbor:
        Atom: {'C': 3, 'H': 1}
    """
    if atom in neighbor_types_map:
        return neighbor_types_map[atom]
    else:
        rval = defaultdict(int)
        for b in atom.bonds:
            kind = b.other_atom(atom).kind
            rval[kind] += 1
        neighbor_types_map[atom] = rval
    return rval


def check_neighbor(neighbor, rule_ids):
    """Ensure that neighbor is valid candidate. """
    rule_ids = set(rule_ids)
    rule_ids.intersection_update(neighbor.opls_whitelist)
    rule_ids.difference_update(neighbor.opls_blacklist)
    return rule_ids


def whitelist(atom, rule):
    """Whitelist an OPLS-aa atomtype for an atom. """
    if isinstance(rule, (list, tuple, set)):
        for r in rule:
            atom.opls_whitelist.add(str(r))
    else:
        atom.opls_whitelist.add(str(rule))


def blacklist(atom, rule):
    """Blacklist an OPLS-aa atomtype for an atom. """
    if isinstance(rule, (list, tuple, set)):
        for r in rule:
            atom.opls_blacklist.add(str(r))
    else:
        atom.opls_blacklist.add(str(rule))


def get_opls_fn(name):
    """Get the full path to a file used to validate the OPLS-aa atomtyper.

    In the source distribution, these files are in ``opls_validation``.

    Args:
        name (str): Name of the file to load.
    """
    fn = resource_filename('mbuild',
                           os.path.join('..', 'opls_validation', name))
    if not os.path.exists(fn):
        raise ValueError('Sorry! {} does not exists. If you just '
                         'added it, you\'ll have to re install'.format(fn))
    return fn


class Rings(object):
    """Find all rings of a specified length that the atom is a part of.

    Note: Finds each ring twice because the graph is traversed in both directions.
    """
    def __init__(self, atom, ring_length):
        """Initialize a ring bearer. """
        self.rings = list()
        self.current_path = list()
        self.branch_points = OrderedSet()
        self.ring_length = ring_length
        self.find_rings(atom)

    def find_rings(self, atom):
        """Find all rings (twice) that this atom is a part of. """
        self.current_path = list()
        self.current_path.append(atom)
        self.step(atom)

    def step(self, atom):
        neighbors = atom.neighbors
        if len(neighbors) > 1:
            if len(neighbors) > 2:
                self.branch_points.add(atom)
            for n in neighbors:
                # Check to see if we found a ring.
                if len(self.current_path) > 2 and n == self.current_path[0]:
                    self.rings.append(copy(self.current_path))
                # Prevent stepping backwards.
                elif n in self.current_path:
                    continue
                else:
                    if len(self.current_path) < self.ring_length:
                        # Take another step.
                        self.current_path.append(n)
                        self.step(n)
                    else:
                        # Reached max length.
                        continue
            else:
                # Finished looping over all neighbors.
                del self.current_path[-1]
                if atom in self.branch_points:
                    self.branch_points.discard(atom)
        else:
            # Found a dead end.
            del self.current_path[-1]

# ----------------------------------------------------#
# Some filters for each element to break up the code #
#----------------------------------------------------#


def carbon(atom):
    valency = len(atom.bonds)
    assert valency < 5, 'Found carbon with valency {}.'.format(valency)

    if valency == 4:
        for rule_id in ['135', '136', '137', '138', '139']:
            run_rule(atom, rule_id)
    elif valency == 3:
        for rule_id in ['141', '142', '143', '145', '145B']:
            run_rule(atom, rule_id)
    else:
        print "Found no rules for {}-valent carbon.".format(valency)


def hydrogen(atom):
    valency = len(atom.bonds)
    assert valency < 2, 'Found hydrogen with valency {}'.format(valency)

    if valency == 1:
        for rule_id in ['140', '144', '146']:
            run_rule(atom, rule_id)
    else:
        print "Found no rules for {}-valent hydrogen".format(valency)


#----------------#
# House of rules #
#----------------#


# Alkanes
def opls_135(atom):
    # alkane CH3
    if neighbor_types(atom)['H'] == 3 and neighbor_types(atom)['C'] == 1:
        whitelist(atom, 135)
        blacklist(atom, [136, 137, 138, 139])


def opls_136(atom):
    # alkane CH2
    if neighbor_types(atom)['H'] == 2 and neighbor_types(atom)['C'] == 2:
        whitelist(atom, 136)
        blacklist(atom, [135, 137, 138, 139])


def opls_137(atom):
    # alkane CH
    if neighbor_types(atom)['H'] == 1 and neighbor_types(atom)['C'] == 3:
        whitelist(atom, 137)
        blacklist(atom, [135, 136, 138, 139])


def opls_138(atom):
    # alkane CH4
    if neighbor_types(atom)['H'] == 4:
        whitelist(atom, 138)
        blacklist(atom, [135, 136, 137, 139])


def opls_139(atom):
    # alkane C
    if neighbor_types(atom)['C'] == 4:
        whitelist(atom, 139)
        blacklist(atom, [135, 136, 137, 138])


def opls_140(atom):
    # alkane H
    if neighbor_types(atom)['C'] == 1:
        whitelist(atom, 140)


# Alkenes
def opls_141(atom):
    # alkene C (R2-C=)
    # TODO: check notation
    if neighbor_types(atom)['C'] == 3:
        whitelist(atom, 141)
        blacklist(atom, [142, 143])


def opls_142(atom):
    # alkene C (RH-C=)
    if neighbor_types(atom)['C'] == 2 and neighbor_types(atom)['H'] == 1:
        whitelist(atom, 142)
        blacklist(atom, [141, 143])


def opls_143(atom):
    # alkene C (H2-C=)
    if neighbor_types(atom)['C'] == 1 and neighbor_types(atom)['H'] == 2:
        whitelist(atom, 143)
        blacklist(atom, [141, 142])


def opls_144(atom):
    # alkene H (H-C=)
    if neighbor_types(atom)['C'] == 1:
        # Make sure that the carbon is an alkene carbon.
        rule_ids = set(['141', '142', '143'])
        if check_neighbor(atom.neighbors[0], rule_ids):
            whitelist(atom, 144)
            blacklist(atom, 140)


# Benzene
def opls_145(atom):
    # Benzene C - 12 site JACS,112,4768-90. Use #145B for biphenyl
    if neighbor_types(atom)['C'] == 2 and neighbor_types(atom)['H'] == 1:
        r = Rings(atom, 6)
        # 2 rings, because we count the traversal in both directions.
        if len(r.rings) == 2:
            for c in r.rings[0]:
                if not (c.kind == 'C' and len(c.neighbors) == 3):
                    break
            else:
                whitelist(atom, 145)
                # Blacklist alkene carbons (with valency 3).
                blacklist(atom, [141, 142, 143])


def opls_145B(atom):
    # Biphenyl C1
    if neighbor_types(atom)['C'] == 3:
        r = Rings(atom, 6)
        # 2 rings, because we count the traversal in both directions.
        if len(r.rings) == 2:
            for c in r.rings[0]:
                if not (c.kind == 'C' and len(c.neighbors) == 3):
                    break
            else:
                for neighbor in atom.neighbors:
                    if neighbor not in r.rings[0]:
                        r = Rings(neighbor, 6)
                        # 2 rings, because we count the traversal in both directions.
                        if len(r.rings) == 2:
                            for c in r.rings[0]:
                                if not (c.kind == 'C' and len(
                                        c.neighbors) == 3):
                                    break
                            else:
                                whitelist(atom, '145B')
                                # Blacklist alkene carbons (with valency 3).
                                blacklist(atom, [141, 142, 143])
                                # Blacklist benzene carbon.
                                blacklist(atom, 145)


def opls_146(atom):
    # Benzene H - 12 site.
    if neighbor_types(atom)['C'] == 1:
        rule_ids = set(['145'])
        if check_neighbor(atom.neighbors[0], rule_ids):
            whitelist(atom, 146)
            blacklist(atom, 144)
            blacklist(atom, 140)


if __name__ == "__main__":
    # m = Alkane(n=3)
    # opls_atomtypes(alkane)
    #
    # for atom in alkane.yield_atoms():
    # print "atom kind={} opls_type={}".format(atom.kind, atom.extras['opls_type'])

    m = Compound()
    # m.append_from_file(get_fn('isopropane.pdb'))
    # m.append_from_file(get_fn('cyclohexane.pdb'))
    # m.append_from_file(get_fn('neopentane.pdb'))
    # m.append_from_file(get_fn('benzene.pdb'))
    # m.append_from_file(get_fn('1-propene.pdb'))
    m.append_from_file(get_opls_fn('biphenyl.pdb'))
    opls_atomtypes(m)

    for atom in m.atoms:
        print "Atom kind={}, opls_whitelist={},  opls_blacklist={}".format(
            atom.kind, atom.opls_whitelist, atom.opls_blacklist)




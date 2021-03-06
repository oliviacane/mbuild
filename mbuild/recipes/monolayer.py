import mbuild as mb


__all__ = ['Monolayer']


class Monolayer(mb.Compound):
    """A general monolayer recipe.

    Parameters
    ----------
    surface : mb.Compound
        Surface on which the monolayer will be built.
    chain : list of mb.Compound
        The chain to be replicated and attached to the surface.
    backfill : list of mb.Compound, optional, default=None
        If there are fewer chains than there are ports on the surface,
        copies of `backfill` will be used to fill the remaining ports.
    pattern : mb.Pattern, optional, default=mb.Random2DPattern
        An array of planar binding locations. If not provided, the entire
        surface will be filled with `chain`.
    tile_x : int, optional, default=1
        Number of times to replicate substrate in x-direction.
    tile_y : int, optional, default=1
        Number of times to replicate substrate in y-direction.

    TODO
    ----
    * Support for arbitrary number of chain types and relative proportions

    """

    def __init__(self, surface, chain, backfill=None, pattern=None, tile_x=1,
                 tile_y=1, **kwargs):
        super(Monolayer, self).__init__()

        # Replicate the surface.
        tiled_compound = mb.TiledCompound(surface, n_tiles=(tile_x, tile_y, 1))
        self.add(tiled_compound, label='tiled_surface')

        if pattern is None:  # Fill the surface.
            pattern = mb.Random2DPattern(len(tiled_compound.referenced_ports()))

        # Attach chains to specified binding sites. Remaining sites get a backfill.
        chains, backfills = pattern.apply_to_compound(guest=chain,
                host=self['tiled_surface'], backfill=backfill, **kwargs)
        self.add(chains)
        self.add(backfills)

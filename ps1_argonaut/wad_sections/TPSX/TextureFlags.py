from enum import IntFlag


class TextureFlags(IntFlag):
    HAS_256_COLORS_PALETTE = 0x80
    IS_NOT_PALETTED = 0x100

    @property
    def n_row(self):
        return ((self.value & 4) >> 1) + ((self.value & 16) >> 4)

    @property
    def n_column(self):
        return self.value & 3

    @property
    def correction_ratio(self):
        """Correction Ratio, needed for non-4bit/pixel textures to be correctly positioned"""
        return (
            4
            if self.IS_NOT_PALETTED in self
            else 2
            if self.HAS_256_COLORS_PALETTE in self
            else 1
        )

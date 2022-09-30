class UnsupportedParsing(NotImplementedError):
    def __init__(self, feature_name):
        super().__init__(
            f"Sorry, {feature_name} parsing / exporting isn't supported (yet) on this game."
        )


class UnsupportedSerialization(NotImplementedError):
    def __init__(self, feature_name):
        super().__init__(
            f"Sorry, {feature_name} serializing isn't supported (yet) on this game."
        )


class ReverseError(Exception):
    def __init__(self, explanation: str, absolute_file_offset: int = None):
        Exception.__init__(self)
        self.message = (
            f"A reversing error has been encountered at offset {hex(absolute_file_offset)}:\n"
            if absolute_file_offset is not None
            else f"A reversing error has been encountered:\n"
        )
        self.message += (
            f"{explanation}\n"
            f"If you think this error isn't supposed to happen, you can ask me for help "
            f"(contact details in the README)."
        )

    def __str__(self):
        return self.message


class SectionNameError(ReverseError):
    def __init__(self, absolute_file_offset: int, expected: str, found: str):
        super().__init__(
            f"Section codename is either missing or incorrect, expected '{expected}', got '{found}'.",
            absolute_file_offset,
        )


class SectionSizeMismatch(ReverseError):
    def __init__(self, absolute_file_offset: int, name: str, expected: int, found: int):
        super().__init__(
            f"The {name} section size is different than expected: got {found} instead of {expected}.",
            absolute_file_offset,
        )


class NegativeIndexError(ReverseError):
    CAUSE_VERTEX = "vertex"
    CAUSE_VERTEX_NORMAL = "vertex normal"
    CAUSE_FACE = "face"

    def __init__(self, absolute_file_offset: int, cause: str, value: int, entire):
        super().__init__(
            f"A negative {cause} index has been found: {value}. Whole {cause}: {entire}",
            absolute_file_offset,
        )


class VerticesNormalsGroupsMismatch(ReverseError):
    def __init__(
        self, n_vertices_groups: int, n_normals_groups: int, absolute_file_offset: int
    ):
        super().__init__(
            f"Different amounts of vertices groups ({n_vertices_groups}) "
            f"and normals groups ({n_normals_groups}) found.",
            absolute_file_offset,
        )


class IncompatibleAnimationError(ReverseError):
    def __init__(self, n_model_vg: int, n_anim_vg: int):
        super().__init__(
            f"This model has {n_model_vg} vertex groups, but "
            f"this animation is designed for models with {n_anim_vg} vertex groups, thus they are incompatible."
        )


class ZeroRunLengthError(ReverseError):
    def __init__(self, absolute_file_offset: int):
        super().__init__(
            "A zero run length has been found while decompressing.",
            absolute_file_offset,
        )


class TexturesWarning(ReverseError):
    def __init__(self, absolute_file_offset: int, n_textures: int, n_rows: int):
        super().__init__(
            f"Too much textures ({n_textures}), or incorrect row count ({n_rows}).\n"
            f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.",
            absolute_file_offset,
        )


class Models3DWarning(ReverseError):
    def __init__(self, absolute_file_offset: int, n_vertices: int, n_faces: int):
        super().__init__(
            f"Too many vertices or faces ({n_vertices} vertices, {n_faces} faces). It is most probably caused by an "
            f"inaccuracy in my reverse engineering of the models format.\nIf you think that the amounts are coherent, "
            f"you can silence this warning with the --ignore-warnings commandline option.",
            absolute_file_offset,
        )


class AnimationsWarning(ReverseError):
    def __init__(self, absolute_file_offset: int, n_total_frames: int):
        super().__init__(
            f"Too much frames in animation (or no frame): {n_total_frames} frames.\n"
            f"It is most probably caused by an inaccuracy in my reverse engineering of the textures format.",
            absolute_file_offset,
        )

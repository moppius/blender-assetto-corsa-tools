from mathutils import Matrix, Quaternion, Vector


def convert_matrix(in_matrix: Matrix):
    co, rotation, scale = in_matrix.decompose()
    co = convert_vector3(co)
    rotation = convert_quaternion(rotation)
    mat_loc = Matrix.Translation(co)
    mat_scale_1 = Matrix.Scale(scale[0], 4, (1, 0, 0))
    mat_scale_2 = Matrix.Scale(scale[2], 4, (0, 1, 0))
    mat_scale_3 = Matrix.Scale(scale[1], 4, (0, 0, 1))
    mat_scale = mat_scale_1 @ mat_scale_2 @ mat_scale_3
    mat_rot = rotation.to_matrix().to_4x4()
    return mat_loc @ mat_rot @ mat_scale


def convert_vector3(in_vec: Vector):
    return Vector((in_vec[0], -in_vec[2], in_vec[1]))


def convert_quaternion(in_quat: Quaternion):
    axis, angle = in_quat.to_axis_angle()
    axis = convert_vector3(axis)
    return Quaternion(axis, angle)

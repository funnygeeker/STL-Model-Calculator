# 基于 https://github.com/mcanet/STL-Volume-Model-Calculator 二次开发
"""
三维模型体积计算
作者: Funnygeeker / Mar Canet
描述: 计算 STL 模型文件的体积，质量，尺寸，三角形数量。
"""
import re      # 正则表达式
import struct  # 结构化数据的处理
from typing import Optional, Union, Tuple  # 数据类型检查


class Materials:
    """
    3D打印材料类，用于存储不同材料的质量和名称。
    """
    def __init__(self):
        # 初始化材料字典
        self.materials_dict = {
            1: {'name': 'ABS', 'density': 1.04},
            2: {'name': 'PLA', 'density': 1.25},
            3: {'name': 'PETG', 'density': 1.27},
            4: {'name': 'PETG-CF', 'density': 1.25}
        }

    def get_density(self, identifier:Union[str, int]) -> float:
        """
        根据材料标识符获取材料的密度。

        Args:
            identifier: 材料的标识符，可以是整数或字符串。
        Returns:
            材料的密度。
        """
        if isinstance(identifier, int) and identifier in self.materials_dict:  # 标识符为数字
            return self.materials_dict[identifier]['density']
        elif isinstance(identifier, str):  # 标识符为文本
            for key, value in self.materials_dict.items():
                if value['name'].lower() == identifier.lower():
                    return value['density']
            raise ValueError(f"Invalid material name: {identifier}")
        else:
            raise ValueError(f"Invalid material identifier: {identifier}")

    def list_materials(self):
        """
        打印所有材料的名称和标识符。
        """
        print("[Materials]")
        for key, value in self.materials_dict.items():
            print(f"{key} = {value['name']}")


class STLUtils:
    """
    STL文件处理工具类，用于读取STL文件并计算体积。
    """
    def __init__(self):
        self._f = None  # 文件对象
        self._volume = None
        self._triangles = []  # 三角形列表
        self.triangles_count = -1  # 三角形数量
        self.is_binary_file = None  # 文件是否为二进制格式

    @staticmethod
    def _is_binary(file) -> bool:
        """
        判断STL文件是否为二进制格式。
        Args:
            file: 文件路径
        Returns:
            如果是二进制格式返回 True，否则返回 False。
        """
        with open(file, 'rb') as f:
            header = f.read(80).decode(errors='replace')
            return not header.startswith('solid')

    def _read_ascii_triangle(self, lines, index):
        """
        从 ASCII 格式的 STL 文件中读取一个三角形的数据。
        Args:
            lines: 文件的每一行
            index: 当前三角形的起始索引
        Returns:
            三角形的体积
        """
        p1 = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", lines[index + 1])))
        p2 = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", lines[index + 2])))
        p3 = list(map(float, re.findall(r"[-+]?\d*\.\d+|\d+", lines[index + 3])))
        return self._signed_volume_of_triangle(p1, p2, p3)

    @staticmethod
    def _signed_volume_of_triangle(p1, p2, p3) -> float:
        """
        计算三角形的体积

        Args:
            p1: 第一个顶点
            p2: 第二个顶点
            p3: 第三个顶点
        Returns:
            三角形的体积
        """
        v321 = p3[0] * p2[1] * p1[2]
        v231 = p2[0] * p3[1] * p1[2]
        v312 = p3[0] * p1[1] * p2[2]
        v132 = p1[0] * p3[1] * p2[2]
        v213 = p2[0] * p1[1] * p3[2]
        v123 = p1[0] * p2[1] * p3[2]
        return (1.0 / 6.0) * (-v321 + v231 + v312 - v132 - v213 + v123)

    def _unpack(self, sig, l):
        """
        解包二进制数据。

        Args:
            sig: 数据格式
            l: 数据长度
        Returns:
            解包后的数据
        """
        s = self._f.read(l)
        return struct.unpack(sig, s)

    def _read_triangle(self):
        """
        从二进制 STL 文件中读取一个三角形的数据。
        Returns:
            三角形的三个顶点
        """
        n = self._unpack("<3f", 12)
        p1 = self._unpack("<3f", 12)
        p2 = self._unpack("<3f", 12)
        p3 = self._unpack("<3f", 12)
        self._unpack("<h", 2)
        return p1, p2, p3

    def _read_length(self):
        """
        读取 STL 文件中的数据长度（三角形数量）
        Returns:
            数据长度（三角形数量）
        """
        length = struct.unpack("@i", self._f.read(4))
        return length[0]

    def _read_header(self):
        """
        跳过 STL 文件的头部信息
        """
        self._f.seek(self._f.tell() + 80)

    @staticmethod
    def cm3_to_inch3(v:float):
        """
        将体积单位从立方厘米转换为立方英寸。

        Args:
            v: 体积（立方厘米）
        Returns:
            体积（立方英寸）
        """
        return v * 0.0610237441

    def load_stl(self, file:str):
        """
        加载 STL 文件并读取三角形数据。

        Returns:
            file: 文件路径
        """
        self.is_binary_file = self._is_binary(file)
        self._triangles = []
        try:
            if self.is_binary_file:
                self._f = open(file, "rb")
                self._read_header()
                self.triangles_count = self._read_length()
                # print(f"[INFO] Total Triangles / 三角形总数: {self.triangles_count}")
                for _ in range(self.triangles_count):
                    self._triangles.append(self._read_triangle())
            else:  # TODO [ERROR] STL file loading failed: list index out of range
                with open(file, 'r') as f:
                    lines = f.readlines()
                i = 0
                while i < len(lines):
                    print(i)
                    if lines[i].strip().startswith('facet'):
                        self._triangles.append(self._read_ascii_triangle(lines, i))
                        i += 7  # 跳过到下一个 facet
                    else:
                        i += 1
                self.triangles_count = len(self._triangles)

        except Exception as e:
            print(f"[ERROR] STL file loading failed: {e}")
            self._triangles = []

    # STL工具类中的方法
    def calculate_volume(self) -> Optional[float]:
        """
        计算 STL 模型的总体积。

        Returns:
            模型文件的体积
        """
        if not self._triangles:
            print("[ERROR] No triangles loaded. Please load the STL file first.")
            return None
        if self._volume is None:
            self._volume = sum(self._signed_volume_of_triangle(p1, p2, p3) for p1, p2, p3 in self._triangles) / 1000  # 将立方毫米转换为立方米
            # print("[INFO] Total volume / 总体积:", self._volume, "cm^3")

        return self._volume


    def calculate_mass(self, density:float) -> Optional[float]:
        """
        计算 STL 模型的总质量。

        Args:
            density: 使用的材料密度，用于计算总质量

        Returns:
            质量数值，-1 为计算失败
        """
        volume = self.calculate_volume()
        mass = volume * density  # 计算总质量

        if mass <= 0:
            print('[WARN] Total mass could not be calculated.')  # 如果计算结果不合理，则输出错误信息
            return -1
        else:
            # print('[INFO] Total mass / 总质量:', mass, 'g')  # 输出总质量
            return mass

    def calculate_area(self) -> Optional[float]:
        """
        计算 STL 模型的表面积。

        Returns:
            表面积（平方厘米）
        """
        if not self._triangles:
            print("[ERROR] No triangles loaded. Please load the STL file first.")
            return None

        area = 0
        for p1, p2, p3 in self._triangles:
            # 计算两个边的向量
            ax, ay, az = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
            bx, by, bz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
            # 计算法向量
            cx, cy, cz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            # 计算一个三角形的面积并累加
            area += 0.5 * (cx * cx + cy * cy + cz * cz) ** 0.5
        area_cm2 = area / 100  # 将平方毫米转换为平方厘米
        # print("[INFO] Total area / 总表面积:", area_cm2, "cm^2")  # 输出总表面积
        return area_cm2

    def calculate_triangles(self) -> Optional[int]:
        """
        计算三角形数量

        Returns:
            三角形数量
        """
        if not self._triangles:
            print("[ERROR] No triangles loaded. Please load the STL file first.")
            return None
        return self.triangles_count

    def calculate_dimensions(self) -> Optional[Tuple[float, float, float]]:
        """
        计算 STL 模型的长、宽和高。

        Returns:
            长、宽、高（以元组形式返回）
        """
        if not self._triangles:
            print("[ERROR] No triangles loaded. Please load the STL file first.")
            return None

        # 初始化最小和最大坐标
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

        # 遍历所有三角形的顶点
        for p1, p2, p3 in self._triangles:
            for point in (p1, p2, p3):
                min_x = min(min_x, point[0])
                min_y = min(min_y, point[1])
                min_z = min(min_z, point[2])
                max_x = max(max_x, point[0])
                max_y = max(max_y, point[1])
                max_z = max(max_z, point[2])

        # 计算长、宽、高
        length = max_x - min_x
        width = max_y - min_y
        height = max_z - min_z

        # print(f"[INFO] Dimensions / 尺寸: X: {length} cm, Y: {width} cm, Z: {height} cm")
        return length, width, height

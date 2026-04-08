"""课程先修关系图分析服务"""

import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Any
from pathlib import Path


@dataclass
class CourseNode:
    """课程节点"""
    course_code: str
    course_name: str
    credits: float
    semester: str  # 开课学期
    prerequisites: List[str]  # 先修课代码列表
    successors: List[str]  # 后续课程代码列表
    blocking_score: int = 0  # 阻塞系数（计算得出）
    

class PrerequisiteGraph:
    """课程先修关系图"""
    
    def __init__(self, prerequisites_data: Optional[List[Dict]] = None):
        self.nodes: Dict[str, CourseNode] = {}
        self._adj_list: Dict[str, Set[str]] = {}  # 邻接表：课程 -> 后继
        self._rev_adj_list: Dict[str, Set[str]] = {}  # 反向邻接表：课程 -> 先修
        
        if prerequisites_data:
            self.build_from_data(prerequisites_data)
            
    def build_from_data(self, data: List[Dict]):
        """从JSON数据构建图"""
        for item in data:
            code = item.get("course_code")
            name = item.get("course_name", "")
            credits = item.get("credits", 0.0)
            semester = item.get("semester", "未知")
            prereqs = item.get("prerequisites", [])
            
            # 创建节点
            self.nodes[code] = CourseNode(
                course_code=code,
                course_name=name,
                credits=credits,
                semester=semester,
                prerequisites=prereqs,
                successors=[]
            )
            
            # 构建邻接表
            self._adj_list[code] = set()
            self._rev_adj_list[code] = set(prereqs)
        
        # 构建后继关系
        for item in data:
            code = item.get("course_code")
            prereqs = item.get("prerequisites", [])
            for prereq in prereqs:
                if prereq in self._adj_list:
                    self._adj_list[prereq].add(code)
                    if code in self.nodes:
                        self.nodes[code].successors.append(prereq)
        
        # 计算阻塞系数
        self.compute_blocking_scores()
        
    def add_course(self, course: CourseNode):
        """添加课程节点"""
        self.nodes[course.course_code] = course
        if course.course_code not in self._adj_list:
            self._adj_list[course.course_code] = set()
        if course.course_code not in self._rev_adj_list:
            self._rev_adj_list[course.course_code] = set(course.prerequisites)
        
    def compute_blocking_scores(self) -> Dict[str, int]:
        """
        计算所有课程的阻塞系数
        
        阻塞系数 = 该课程可达的所有后继节点数量
        意义：不修这门课会阻塞多少后续课程
        """
        blocking_scores = {}
        
        for code in self.nodes:
            # BFS计算可达后继节点
            visited = set()
            queue = [code]
            score = 0
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                
                if current != code:  # 不计算自己
                    score += 1
                
                # 添加后继到队列
                for successor in self._adj_list.get(current, set()):
                    if successor not in visited:
                        queue.append(successor)
            
            blocking_scores[code] = score
            if code in self.nodes:
                self.nodes[code].blocking_score = score
        
        return blocking_scores
        
    def get_prerequisites_for_course(self, course_code: str) -> List[str]:
        """获取某门课的所有先修课（递归）"""
        if course_code not in self.nodes:
            return []
        
        all_prereqs = []
        visited = set()
        queue = [course_code]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # 添加直接先修课
            prereqs = self._rev_adj_list.get(current, set())
            for prereq in prereqs:
                if prereq not in visited:
                    all_prereqs.append(prereq)
                    queue.append(prereq)
        
        return all_prereqs
        
    def get_available_courses(
        self,
        completed_courses: List[str],
        target_semester: str
    ) -> List[str]:
        """
        获取当前可选课程
        条件：
        1. 先修课已全部完成
        2. 在本学期开课
        3. 未修过或可以重修
        """
        available = []
        completed_set = set(completed_courses)
        
        for code, node in self.nodes.items():
            # 检查是否已修过
            if code in completed_set:
                continue
            
            # 检查先修课是否完成
            prereqs_satisfied = all(
                prereq in completed_set 
                for prereq in node.prerequisites
            )
            
            if prereqs_satisfied:
                available.append(code)
        
        return available
        
    def topological_sort(self) -> List[str]:
        """拓扑排序，返回课程学习顺序"""
        # Kahn算法
        in_degree = {code: len(self._rev_adj_list.get(code, set())) 
                     for code in self.nodes}
        queue = [code for code, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            code = queue.pop(0)
            result.append(code)
            
            for successor in self._adj_list.get(code, set()):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
        
        # 如果有剩余节点，说明有环
        if len(result) != len(self.nodes):
            # 添加剩余节点（有环的情况）
            for code in self.nodes:
                if code not in result:
                    result.append(code)
        
        return result
        
    def visualize_path(self, target_course: str) -> List[str]:
        """
        可视化到目标课程的学习路径
        返回从起点到目标课程的路径
        """
        if target_course not in self.nodes:
            return []
        
        # BFS找最短路径
        queue = [(target_course, [target_course])]
        visited = {target_course}
        
        while queue:
            current, path = queue.pop(0)
            
            # 如果没有先修课，返回路径
            if not self._rev_adj_list.get(current):
                return path[::-1]  # 反转，从起点到目标
            
            for prereq in self._rev_adj_list[current]:
                if prereq not in visited:
                    visited.add(prereq)
                    queue.append((prereq, path + [prereq]))
        
        return []
    
    def get_blocking_courses(self, min_score: int = 3) -> List[CourseNode]:
        """获取高阻塞系数的课程（关键课程）"""
        return sorted(
            [node for node in self.nodes.values() if node.blocking_score >= min_score],
            key=lambda x: x.blocking_score,
            reverse=True
        )


def load_prerequisite_graph(data_path: Optional[str] = None) -> PrerequisiteGraph:
    """加载先修关系图"""
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data" / "courses" / "prerequisites.json"
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return PrerequisiteGraph(data.get("prerequisites", []))

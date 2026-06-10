import yaml
import os

# 仅由 test_agent_routing 加载，test_single_turn 扫描 data/ 时自动排除
AGENT_ROUTING_FILES = frozenset({"agent_routing.yml", "agent_routing.yaml"})


def load_yaml_data(path, exclude_files=None):
    """
    高级数据加载引擎：
    支持读取单一 YAML 文件，也支持扫描整个文件夹下的所有 YAML 文件。
    """
    valid_cases = []
    skip_files = exclude_files or frozenset()

    # 场景一：传入文件列表，逐个读取
    if isinstance(path, (list, tuple)):
        for item in path:
            valid_cases.extend(load_yaml_data(item, exclude_files=skip_files))
        return valid_cases

    # 相对路径转绝对路径
    if not os.path.isabs(path):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_path = os.path.join(root_dir, path)
    else:
        target_path = path

    # 场景二：传入文件夹，扫描其中所有 .yml / .yaml
    if os.path.isdir(target_path):
        for file_name in sorted(os.listdir(target_path)):
            if not file_name.endswith((".yml", ".yaml")):
                continue
            if file_name in skip_files:
                continue
            file_path = os.path.join(target_path, file_name)
            valid_cases.extend(_read_single_yaml(file_path))

    # 场景三：传入单个文件
    elif os.path.isfile(target_path):
        valid_cases.extend(_read_single_yaml(target_path))

    else:
        print(f"警告：路径不存在，请检查 -> {target_path}")

    return valid_cases


def load_single_turn_cases(path="data/"):
    """
    单轮评测用例：扫描 data/，但排除 agent_routing.yml，并跳过带 mock_file 的条目。
    带 WireMock 的 Agent 路由场景统一交给 test_agent_routing。
    """
    cases = load_yaml_data(path, exclude_files=AGENT_ROUTING_FILES)
    return [case for case in cases if not case.get("mock_file")]


def load_agent_routing_cases(path="data/agent_routing.yml"):
    """Agent 路由评测用例：仅加载 agent_routing.yml，且必须配置 mock_file。"""
    cases = load_yaml_data(path)
    return [case for case in cases if case.get("mock_file")]


def _read_single_yaml(file_path):
    """内部辅助方法：读取单个文件并做格式校验"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data:
        return []

    cases = []
    for case in data:
        if case.get("case_id") and case.get("prompt"):
            cases.append(case)
        else:
            print(f"警告：发现缺失 case_id 或 prompt 的无效用例，已自动跳过 -> {case}")
    return cases


if __name__ == "__main__":
    # 测试一下读取整个文件夹
    all_cases = load_yaml_data("data/")
    print(f"扫描文件夹，共读取到 {len(all_cases)} 条用例")

    # 测试一下只读取一个文件
    agent_cases = load_yaml_data("data/agent.yml")
    print(f"读取单文件，共读取到 {len(agent_cases)} 条用例")
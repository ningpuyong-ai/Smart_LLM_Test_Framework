import yaml
import os


def load_yaml_data(path):
    """
    高级数据加载引擎：
    支持读取单一 YAML 文件，也支持扫描整个文件夹下的所有 YAML 文件。
    """
    # 如果传进来的是相对路径，转成绝对路径
    if not os.path.isabs(path):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 往上级退两层 回到根目录
        target_path = os.path.join(root_dir, path)  # 用根目录 + 相对路径 拼成绝对路径
    else:
        target_path = path

    valid_cases = []

    # 场景一：如果传入的是一个文件夹目录，则扫描里面所有的 .yml 文件
    if os.path.isdir(target_path):
        for file_name in os.listdir(target_path):
            if file_name.endswith(('.yml', '.yaml')):
                file_path = os.path.join(target_path, file_name)
                valid_cases.extend(_read_single_yaml(file_path))

    # 场景二：如果传入的是具体的单一文件，直接读取
    elif os.path.isfile(target_path):
        valid_cases.extend(_read_single_yaml(target_path))

    else:
        print(f"警告：路径不存在，请检查 -> {target_path}")

    return valid_cases


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
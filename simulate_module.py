# -*- coding:utf-8 _*-
import ctypes
import os


def load_instructions_from_file(sample_path):
    assert os.path.exists(sample_path), sample_path + \
        " 路径下不存在该文件"  # assert()如果条件返回错误，则终止程序执行
    with open(sample_path) as f:
        lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].strip()  # strip()的参数为空，默认删除字符串头和尾的空白字符
            # print(lines[i])
        return lines
    return []


def get_max_width_of_address(instructions, init_pos):
    last_pos = init_pos + 4 * (len(instructions) - 1)  # 最后的内存地址
    return len(str(last_pos))


def format_address_with_width(address):
    format_str = "%-" + str(MAX_WIDTH_OF_ADDRESS) + "d"
    return format_str % address


def binary_str2int(string):
    if string[0] == '1':
        return int(string, 2) - 2 ** len(string)
    else:
        return int(string, 2)


def get_data_address(instructions, init_pos):
    last_break_index = -1
    for i in range(len(instructions)):
        if is_break(instructions[i]):
            last_break_index = i

    assert last_break_index != -1, "没有break语句"
    data_start_pos = init_pos + 4 * (last_break_index + 1)
    return data_start_pos


def init_cache(data_instruction, data_start_pos):
    cache = {}  # 字典
    # init Register
    for i in range(32):
        cache['R' + str(i)] = 0
        # 所有寄存器设为0
    num_data = len(data_instruction)
    pos = data_start_pos
    for i in range(num_data):
        cache[pos] = binary_str2int(data_instruction[i])
        pos += 4
    cache['stop_read_instruction'] = False
    cache['IF Unit:Waiting Instruction'] = []
    cache['IF Unit:Executed Instruction'] = []
    cache['Pre-Issue Buffer'] = []
    cache['Pre-ALU Queue'] = []
    cache['Post-ALU Buffer'] = []
    cache['Pre-ALUB Queue'] = []
    cache['Post-ALUB Buffer'] = []
    cache['Pre-MEM Queue'] = []
    cache['Post-MEM Buffer'] = []
    return cache


def split_instruction(instruction, len_arr):
    if not isinstance(instruction, str):
        instruction = instruction[1]
    assert len(instruction) == sum(len_arr), instruction + \
        " 指令长度不是" + str(sum(len_arr))
    pos = 0
    arr = []
    for length in len_arr:
        arr.append(instruction[pos: pos + length])
        pos += length
    return arr


def get_R_name(binary_str):
    return "R" + str(int(binary_str, 2))


def is_break(instruction):
    arr = split_instruction(instruction, [6, 20, 6])
    return arr[0] == "000000" and arr[2] == "001101"


def execute_break(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 20, 6])
    next_pos = instruction_pos + 4
    if execute:
        desc = str(instruction_pos) + "\t" + "BREAK" + \
            "\n\n" + cache_state(cache) + "\n"
        # print(desc)
    else:
        desc = " ".join(format_binary_str(instruction)) + \
            "\t" + str(instruction_pos) + " BREAK"
        # print(desc)
    return desc, next_pos


def ins2str_break(instruction, instruction_pos, cache, execute):
    return "BREAK"


def get_read_and_write_operand_break(instruction):
    return [[], []]


def is_nop(instruction):
    return instruction == "0000" * 8


def execute_nop(instruction, instruction_pos, cache, execute):
    next_pos = instruction_pos + 4
    if execute:
        desc = str(instruction_pos) + "\t" + "NOP" + \
            "\n\n" + cache_state(cache) + "\n"
        # print(desc)
    else:
        desc = " ".join(format_binary_str(instruction)) + \
            "\t" + str(instruction_pos) + " NOP"
    return desc, next_pos


def ins2str_nop(instruction, instruction_pos, cache, execute):
    return "NOP"


def is_category1_J(instruction):
    arr = split_instruction(instruction, [6, 26])
    return arr[0] == "000010"


def execute_category1_J(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 26])
    describe = ""
    if execute:
        next_pos = int(arr[1], 2) * 4
        return describe, next_pos
    else:
        next_pos = int(arr[1], 2) * 4
        describe = " ".join(format_binary_str(instruction)) + \
            "\t" + str(instruction_pos) + " J #" + str(next_pos)
        return describe, instruction_pos + 4


def ins2str_category1_J(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 26])
    next_pos = int(arr[1], 2) * 4
    return "J\t#" + str(next_pos)


def get_read_and_write_operand_category1_J(instruction):
    return [[], []]


def is_category1_JR(instruction):
    arr = split_instruction(instruction, [6, 5, 10, 5, 6])
    return arr[0] == "000010" and arr[2] == "0000000000" and arr[-1] == "001000"


def execute_category1_JR(instruction, instruction_pos, cache, execute):
    arr = arr = split_instruction(instruction, [6, 5, 10, 5, 6])

    address = cache[get_R_name(arr[1])]
    temp = cache[address]
    next_pos = instruction_pos + 4
    desc = ""
    if execute:
        if (cache['Config_ca'] == 0):
            next_pos = temp
        else:
            next_pos = (temp // 2) * 2
            cache['ISAMode'] = temp & 1
    else:
        if (cache['Config_ca'] == 0):
            next_pos = temp
        else:
            next_pos = (temp // 2) * 2
        desc = " ".join(arr) + "\t" + str(instruction_pos) + \
            " J #" + str(next_pos)
        next_pos = instruction_pos + 4
    return desc, next_pos


def ins2str_category1_JR(instruction, instruction_pos, cache, execute):
    arr = arr = split_instruction(instruction, [6, 5, 10, 5, 6])

    address = cache[get_R_name(arr[1])]
    temp = cache[address]
    next_pos = instruction_pos + 4
    return "J\t#" + str(next_pos)


def get_read_and_write_operand_category1_JR(instruction):
    arr = arr = split_instruction(instruction, [6, 5, 10, 5, 6])
    return [[get_R_name(arr[1])], []]


def format_binary_str(instruction):
    arr = [6, 5, 5, 5, 5, 6]
    return split_instruction(instruction, arr)


def is_category1_BEQ(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    return arr[0] == "000100"


def execute_category1_BEQ(instruction, instruction_pos, cache, execute):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    offset = arr[3]
    next_pos = instruction_pos + 4
    target_offset = binary_str2int(offset + "00")
    # print(target_offset)
    desc = ""
    if execute:
        condition = cache[rs] == cache[rt]
        if (condition):
            next_pos = next_pos + target_offset
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " BEQ " + rs + ", " + rt + ", #" + str(target_offset)
    return desc, next_pos


def ins2str_category1_BEQ(instruction, instruction_pos, cache, execute):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    offset = arr[3]
    next_pos = instruction_pos + 4
    target_offset = binary_str2int(offset + "00")
    return "BEQ\t" + rs + ", " + rt + ", #" + str(target_offset)


def get_read_and_write_operand_category1_BEQ(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])

    return [[rs, rt], []]


def is_category1_BGTZ(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    return arr[0] == "000111" and arr[2] == "00000"


def execute_category1_BGTZ(instruction, instruction_pos, cache, execute):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    offset = arr[3]

    target_offset = binary_str2int(offset + "00")
    next_pos = instruction_pos + 4
    desc = ""
    if execute:
        condition = cache[rs] > 0
        if (condition):
            next_pos = next_pos + target_offset
        # desc = str(instruction_pos) + "\t" + "BGTZ " + rs + ", #" + str(target_offset) + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + \
            str(instruction_pos) + " BGTZ " + rs + ", #" + str(target_offset)

    return desc, next_pos


def ins2str_category1_BGTZ(instruction, instruction_pos, cache, execute):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    offset = arr[3]

    target_offset = binary_str2int(offset + "00")
    return "BGTZ\t" + rs + ", #" + str(target_offset)


def get_read_and_write_operand_category1_BGTZ(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])

    return [[rs], []]


def is_category1_BLTZ(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    return arr[0] == "000001" and arr[2] == "00000"


def execute_category1_BLTZ(instruction, instruction_pos, cache, execute):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    offset = arr[3]

    target_offset = binary_str2int(offset + "00")
    next_pos = instruction_pos + 4
    desc = ""
    if execute:
        condition = cache[rs] < 0
        if (condition):
            next_pos = next_pos + target_offset
        # desc = str(instruction_pos) + "" + "BLTZ " + rs + ", #" + str(target_offset) + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + \
            str(instruction_pos) + " BLTZ " + rs + ", #" + str(target_offset)
    return desc, next_pos


def ins2str_category1_BLTZ(instruction, instruction_pos, cache, execute):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])
    offset = arr[3]

    target_offset = binary_str2int(offset + "00")
    next_pos = instruction_pos + 4
    return "BLTZ\t" + rs + ", #" + str(target_offset)


def get_read_and_write_operand_category1_BLTZ(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 16])
    rs = get_R_name(arr[1])

    return [[rs], []]


def is_category1_add(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "000000" and arr[-2] == "00000" and arr[-1] == "100000"


def execute_category1_add(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])

    discribe = ""
    if execute:
        cache[rd] = cache[rs] + cache[rt]
        # discribe = str(instruction_pos) + "\t" + "ADD " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        discribe = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " ADD " + rd + ", " + rs + ", " + rt
    return discribe, instruction_pos + 4


def ins2str_category1_add(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])

    return "ADD\t" + rd + ", " + rs + ", " + rt


def get_read_and_write_operand_category1_add(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return [[rs, rt], [rd]]


def is_category1_sub(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "000000" and arr[-2] == "00000" and arr[-1] == "100010"


def execute_category1_sub(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    discribe = ""
    if execute:
        cache[rd] = cache[rs] - cache[rt]
        # discribe = str(instruction_pos) + "\t" + "SUB " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        discribe = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " SUB " + rd + ", " + rs + ", " + rt
    return discribe, instruction_pos + 4


def ins2str_category1_sub(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])

    return "SUB\t" + rd + ", " + rs + ", " + rt


def get_read_and_write_operand_category1_sub(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return [[rs, rt], [rd]]


def is_category1_mult(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "011100" and arr[-2] == "00000" and arr[-1] == "000010"


def get_read_and_write_operand_category1_mult(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return [[rs, rt], [rd]]


def execute_category1_mult(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    desc = ""
    if execute:
        cache[rd] = cache[rs] * cache[rt]
        # desc = str(instruction_pos) + "\t" + "MUL " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " MUL " + rd + ", " + rs + ", " + rt

    return desc, instruction_pos + 4


def ins2str_category1_mul(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return "MUL\t" + rd + ", " + rs + ", " + rt


def is_category1_LW(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 16])
    return arr[0] == "100011"


def execute_category1_LW(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 16])

    base_name = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    offset = binary_str2int(arr[3])
    desc = ""
    if execute:
        cache[rt] = cache[offset + cache[base_name]]
        # desc = str(instruction_pos) + "\t" + "LW " + rt + ", " + str(
        # offset) + "(" + base_name + ")" + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " LW " + rt + ", " + str(offset) + "(" + base_name + ")"
    return desc, instruction_pos + 4


def ins2str_category1_LW(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 16])

    base_name = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    offset = binary_str2int(arr[3])
    return "LW\t" + rt + ", " + str(offset) + "(" + base_name + ")"


def get_read_and_write_operand_category1_LW(instruction, cache):
    arr = split_instruction(instruction, [6, 5, 5, 16])

    base_name = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    offset = binary_str2int(arr[3])
    return [[base_name, offset + cache[base_name]], [rt]]


def is_category1_SW(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 16])
    return arr[0] == "101011"


def execute_category1_SW(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 16])
    desc = ""
    base_name = get_R_name(arr[1])

    rt = get_R_name(arr[2])
    offset = binary_str2int(arr[3])
    if execute:
        cache[offset + cache[base_name]] = cache[rt]
        # desc = str(instruction_pos) + "\t" + "SW " + rt + ", " + str(
        # offset) + "(" + base_name + ")" + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " SW " + rt + ", " + str(offset) + "(" + base_name + ")"

    return desc, instruction_pos + 4


def get_read_and_write_operand_category1_SW(instruction, cache):
    arr = split_instruction(instruction, [6, 5, 5, 16])
    desc = ""
    base_name = get_R_name(arr[1])

    rt = get_R_name(arr[2])
    offset = binary_str2int(arr[3])
    return [[rt, base_name], [offset + cache[base_name]]]


def ins2str_category1_SW(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 16])
    desc = ""
    base_name = get_R_name(arr[1])

    rt = get_R_name(arr[2])
    offset = binary_str2int(arr[3])
    return "SW\t" + rt + ", " + str(offset) + "(" + base_name + ")"


def is_category1_SLL(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "000000" and arr[1] == "00000" and arr[-1] == "000000"


def execute_category1_SLL(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    desc = ""
    if execute:
        cache[rd] = cache[rt] << sa
        # desc = str(instruction_pos) + "\t" + "SLL " + rd + ", " + rt + ", #" + str(sa) + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " SLL " + rd + ", " + rt + ", #" + str(sa)
    return desc, instruction_pos + 4


def ins2str_category1_SLL(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return "SLL\t" + rd + ", " + rt + ", #" + str(sa)


def get_read_and_write_operand_category1_SLL(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return [[rt], [rd]]


def is_category1_SRL(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "000000" and arr[1] == "00000" and arr[-1] == "000010"


# 32位逻辑右移
def unsigned32_right_shitf(x, offset):
    assert offset >= 0, "negative shift count"
    return (x & (2 ** 32 - 1)) >> offset


def execute_category1_SRL(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    desc = ""
    if execute:
        cache[rd] = unsigned32_right_shitf(cache[rt], sa)
        # desc = str(instruction_pos) + "\t" + "SRL " + rd + ", " + rt + ", #" + str(sa) + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " SRL " + rd + ", " + rt + ", #" + str(sa)
    return desc, instruction_pos + 4


def ins2str_category1_SRL(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return "SRL\t" + rd + ", " + rt + ", #" + str(sa)


def get_read_and_write_operand_category1_SRL(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return [[rt], [rd]]


def is_category1_SRA(instruction):
    # 前
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "000000" and arr[1] == "00000" and arr[-1] == "000011"


def execute_category1_SRA(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    desc = ""
    if execute:
        cache[rd] = cache[rt] >> sa
        # desc = str(instruction_pos) + "\t" + "SRA " + rd + ", " + rt + ", #" + str(sa) + "\n\n" + cache_state(
        #     cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " SRA " + rd + ", " + rt + ", #" + str(sa)
    return desc, instruction_pos + 4


def ins2str_category1_SRA(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    return "SRA\t" + rd + ", " + rt + ", #" + str(sa)


def get_read_and_write_operand_category1_SRA(instruction):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    sa = int(arr[4], 2)
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])

    return [[rt], [rd]]


def is_category2_add(instruction):
    # 前六位
    arr = split_instruction(instruction, [1, 5, 5, 5, 5, 5, 6])
    return arr[1] == "10000"


def execute_category2_add(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        if execute:
            cache[rd] = cache[rs] + cache[rt]
            # desc = str(instruction_pos) + "\t" + "ADD " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
            #     cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " ADD " + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = cache[rs] + immediate
            desc = ""
            # desc = str(instruction_pos) + "\t" + "ADD " + rt + ", " + rs + ", #" + str(
            #     immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " ADD " + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def ins2str_category2_add(instruction, instruction_pos, cache, execute):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return "ADD\t" + rd + ", " + rs + ", " + rt

    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        return "ADD\t" + rt + ", " + rs + ", #" + str(immediate)


def get_read_and_write_operand_category2_add(instruction):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return [[rs, rt], [rd]]
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        return [[rs], [rt]]


def is_category2_sub(instruction):
    # 前六位
    arr = split_instruction(instruction, [1, 5, 5, 5, 5, 5, 6])
    return arr[1] == "10001"


def execute_category2_sub(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        if execute:
            cache[rd] = cache[rs] - cache[rt]
            # desc = str(instruction_pos) + "\t" + "SUB " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
            #     cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " SUB " + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = cache[rs] - immediate
            desc = str(instruction_pos) + "\t" + "SUB " + rt + ", " + rs + \
                ", #" + str(immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " SUB " + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def ins2str_category2_sub(instruction, instruction_pos, cache, execute):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return "SUB\t" + rd + ", " + rs + ", " + rt
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        return "SUB\t" + rt + ", " + rs + ", #" + str(immediate)


def get_read_and_write_operand_category2_sub(instruction):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return [[rs, rt], [rd]]
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        return [[rs], [rt]]


def is_category2_mul(instruction):
    arr = split_instruction(instruction, [1, 5, 5, 5, 5, 5, 6])
    return arr[1] == "00001"


def execute_category2_mul(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        if execute:
            cache[rd] = cache[rs] * cache[rt]
            # desc = str(instruction_pos) + "\t" + "MUL " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
            #     cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " MUL " + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = cache[rs] * immediate
            desc = str(instruction_pos) + "\t" + "MUL " + rt + ", " + rs + \
                ", #" + str(immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " MUL " + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def ins2str_category2_mul(instruction, instruction_pos, cache, execute):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return "MUL\t" + rd + ", " + rs + ", " + rt
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        return "MUL\t" + rt + ", " + rs + ", #" + str(immediate)


def get_read_and_write_operand_category2_mul(instruction):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])

        return [[rs, rt], [rd]]
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        return [[rs], [rt]]


def is_category2_and(instruction):
    arr = split_instruction(instruction, [1, 5, 5, 5, 5, 5, 6])
    return arr[1] == "10010"


def execute_category2_and(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        if execute:
            cache[rd] = cache[rs] & cache[rt]
            # desc = str(instruction_pos) + "\t" + "AND " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
            #     cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " AND " + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = cache[rs] & immediate
            desc = str(instruction_pos) + "\t" + "AND " + rt + ", " + rs + \
                ", #" + str(immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " AND " + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def ins2str_category2_and(instruction, instruction_pos, cache, execute):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return "AND\t" + rd + ", " + rs + ", " + rt
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        return "AND\t" + rt + ", " + rs + ", #" + str(immediate)


def get_read_and_write_operand_category2_and(instruction):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])

        return [[rs, rt], [rd]]
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        return [[rs], [rt]]


def is_category2_nor(instruction):
    arr = split_instruction(instruction, [1, 5, 5, 5, 5, 5, 6])
    return arr[1] == "10011"


def execute_category2_nor(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        if execute:
            cache[rd] = (cache[rs] ^ -1) & (cache[rt] ^ -1)
            # desc = str(instruction_pos) + "\t" + "NOR " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
            #     cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " NOR " + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = (cache[rs] ^ -1) & (immediate ^ -1)
            desc = str(instruction_pos) + "\t" + "NOR " + rt + ", " + rs + \
                ", #" + str(immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " NOR " + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def ins2str_category2_nor(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return "NOR\t" + rd + ", " + rs + ", " + rt
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        return "NOR\t" + rt + ", " + rs + ", #" + str(immediate)


def get_read_and_write_operand_category2_nor(instruction):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])

        return [[rs, rt], [rd]]
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        return [[rs], [rt]]


def is_category2_SLT(instruction):
    arr = split_instruction(instruction, [1, 5, 5, 5, 5, 5, 6])
    return arr[1] == "10101"


def execute_category2_SLT(instruction, instruction_pos, cache, execute):
    desc = ""
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        if execute:
            cache[rd] = (cache[rs] ^ -1) & cache[rt]
            # desc = str(instruction_pos) + "\t" + "SLT " + rd + ", " + rs + ", " + rt + "\n\n" + cache_state(
            #     cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " SLT " + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = (cache[rs] ^ -1) & immediate
            desc = str(instruction_pos) + "\t" + "SLT " + rt + ", " + rs + \
                ", #" + str(immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + " SLT " + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def ins2str_category2_SLT(instruction, instruction_pos, cache, execute):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])
        return "SLT\t" + rd + ", " + rs + ", " + rt

    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        return "SLT " + rt + ", " + rs + ", #" + str(immediate)


def get_read_and_write_operand_category2_SLT(instruction):
    if (instruction[0] == '0'):
        arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
        rs = get_R_name(arr[1])
        rt = get_R_name(arr[2])
        rd = get_R_name(arr[3])

        return [[rs, rt], [rd]]
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        return [[rs], [rt]]


def execute_int(instructions, init_pos, instruction_pos, content):
    instruction = instructions[(instruction_pos - init_pos) // 4]

    num = binary_str2int(instruction)
    content.append(
        instruction +
        "\t" +
        format_address_with_width(instruction_pos) +
        " " +
        str(num))
    return instruction_pos + 4


def ins2str(instructions, pos_ins_pair, init_pos, cache):
    return ins2str_impl(instructions, pos_ins_pair, init_pos, cache)


def ins2str_impl(instructions, pos_ins_pair, init_pos, cache):
    execute = False
    instruction_pos = pos_ins_pair[0]
    instruction = instructions[(instruction_pos - init_pos) // 4]

    if (is_category1_add(instruction)):
        return ins2str_category1_add(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_J(instruction)):
        return ins2str_category1_J(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_JR(instruction)):
        return ins2str_category1_JR(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_BEQ(instruction)):
        return ins2str_category1_BEQ(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SLL(instruction)):
        return ins2str_category1_SLL(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_LW(instruction)):
        return ins2str_category1_LW(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_mult(instruction)):
        return ins2str_category1_mul(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_BGTZ(instruction)):
        return ins2str_category1_BGTZ(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_sub(instruction)):
        return ins2str_category1_sub(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SW(instruction)):
        return ins2str_category1_SW(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_BLTZ(instruction)):
        return ins2str_category1_BLTZ(
            instruction, instruction_pos, cache, execute)
    elif (is_break(instruction)):
        return ins2str_break(instruction, instruction_pos, cache, execute)
    elif (is_category1_SRA(instruction)):
        return ins2str_category1_SRA(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SRL(instruction)):
        return ins2str_category1_SRL(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_add(instruction)):
        return ins2str_category2_add(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_sub(instruction)):
        return ins2str_category2_sub(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_mul(instruction)):
        return ins2str_category2_mul(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_and(instruction)):
        return ins2str_category2_and(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_nor(instruction)):
        return ins2str_category2_nor(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_SLT(instruction)):
        return ins2str_category2_SLT(
            instruction, instruction_pos, cache, execute)
    else:
        assert False, "没有匹配指令"


def cache_state(cache):
    return ""
    # 永远都不会运行到，但语法上要加上


def cache_state(instructions, init_pos, cache):

    def ins2str2(pos_ins_pair):
        return ins2str(instructions, pos_ins_pair, init_pos, cache)

    def if_unit(cache):
        ret = ""
        ret = ret + "IF Unit:\n\tWaiting Instruction: "
        if(len(cache['IF Unit:Waiting Instruction']) != 0):
            ret = ret + ins2str2(cache['IF Unit:Waiting Instruction'][0])

        ret = ret + "\n"
        ret = ret + "\tExecuted Instruction: "
        if (len(cache['IF Unit:Executed Instruction']) != 0):
            ret = ret + ins2str2(cache['IF Unit:Executed Instruction'][0])
        ret = ret + "\n"
        return ret

    def pre_issur_buffer(cache):
        ret = ""
        ret = ret + "Pre-Issue Buffer:\n"
        for i in range(4):
            ret = ret + "\tEntry " + str(i) + ":"
            if i < len(cache['Pre-Issue Buffer']):
                ret = ret + "[" + ins2str2(cache['Pre-Issue Buffer'][i]) + "]"
            ret = ret + "\n"
        return ret

    def pre_alu_queue(cache):
        ret = ""
        ret = ret + "Pre-ALU Queue:\n"
        for i in range(2):
            ret = ret + "\tEntry " + str(i) + ":"
            if i < len(cache['Pre-ALU Queue']):
                ret = ret + "[" + ins2str2(cache['Pre-ALU Queue'][i]) + "]"
            ret = ret + "\n"
        return ret

    def post_alu_buffer(cache):
        ret = ""
        ret = ret + "Post-ALU Buffer:"

        if (len(cache['Post-ALU Buffer']) == 1):
            ret = ret + "[" + ins2str2(cache['Post-ALU Buffer'][0]) + "]"
        ret = ret + "\n"
        return ret

    def pre_alub_queue(cache):
        ret = ""
        ret = ret + "Pre-ALUB Queue:\n"
        for i in range(2):
            ret = ret + "\tEntry " + str(i) + ":"
            if i < len(cache['Pre-ALUB Queue']):
                ret = ret + "[" + ins2str2(cache['Pre-ALUB Queue'][i]) + "]"
            ret = ret + "\n"
        return ret

    def post_alub_buffer(cache):
        ret = ""
        ret = ret + "Post-ALUB Buffer:"

        if (len(cache['Post-ALUB Buffer']) == 1):
            ret = ret + "[" + ins2str2(cache['Post-ALUB Buffer'][0]) + "]"
        ret = ret + "\n"
        return ret

    def pre_mem_queue(cache):
        ret = ""
        ret = ret + "Pre-MEM Queue:\n"
        for i in range(2):
            ret = ret + "\tEntry " + str(i) + ":"
            if i < len(cache['Pre-MEM Queue']):
                ret = ret + "[" + ins2str2(cache['Pre-MEM Queue'][i]) + "]"
            ret = ret + "\n"
        return ret

    def post_mem_buffer(cache):
        ret = ""
        ret = ret + "Post-MEM Buffer:"

        if (len(cache['Post-MEM Buffer']) == 1):
            ret = ret + "[" + ins2str2(cache['Post-MEM Buffer'][0]) + "]"
        ret = ret + "\n"
        return ret

    state = if_unit(cache) + pre_issur_buffer(cache) + pre_alu_queue(cache) + post_alu_buffer(cache) + \
        pre_alub_queue(cache) + post_alub_buffer(cache) + pre_mem_queue(cache) + post_mem_buffer(cache)

    state = state + "\n"

    data_address = DATA_ADDRESS
    state = state + "Registers\n"

    for row in range(4):
        state = state + ("R%02d:" % (row * 8))
        for col in range(8):
            state = state + '\t' + str(cache['R' + str(row * 8 + col)])
        state = state + "\n"

    Data = "\nData\n"
    address = data_address
    while cache.get(address) is not None:
        Data = Data + str(address) + ":"
        for _ in range(8):
            if cache.get(address) is not None:
                Data = Data + "\t" + str(cache[address])
                address = address + 4
        Data = Data + "\n"
    state = state + Data
    state = state[:-1]
    return state


# 执行一条指令后，返回下一条指令的地址
def execute_one_instruction(
        instructions,
        instruction_pos,
        init_pos,
        cache,
        content,
        execute,
        circle):
    instruction = instructions[(instruction_pos - init_pos) // 4]
    instruction_description = ""
    next_instruction_pos = -1

    if (is_category1_add(instruction)):
        instruction_description, next_instruction_pos = execute_category1_add(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_J(instruction)):
        instruction_description, next_instruction_pos = execute_category1_J(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_JR(instruction)):
        instruction_description, next_instruction_pos = execute_category1_JR(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_BEQ(instruction)):
        instruction_description, next_instruction_pos = execute_category1_BEQ(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SLL(instruction)):
        instruction_description, next_instruction_pos = execute_category1_SLL(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_LW(instruction)):
        instruction_description, next_instruction_pos = execute_category1_LW(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_mult(instruction)):
        instruction_description, next_instruction_pos = execute_category1_mult(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_BGTZ(instruction)):
        instruction_description, next_instruction_pos = execute_category1_BGTZ(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_sub(instruction)):
        instruction_description, next_instruction_pos = execute_category1_sub(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SW(instruction)):
        instruction_description, next_instruction_pos = execute_category1_SW(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_BLTZ(instruction)):
        instruction_description, next_instruction_pos = execute_category1_BLTZ(
            instruction, instruction_pos, cache, execute)
    elif (is_break(instruction)):
        instruction_description, next_instruction_pos = execute_break(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SRA(instruction)):
        instruction_description, next_instruction_pos = execute_category1_SRA(
            instruction, instruction_pos, cache, execute)
    elif (is_category1_SRL(instruction)):
        instruction_description, next_instruction_pos = execute_category1_SRL(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_add(instruction)):
        instruction_description, next_instruction_pos = execute_category2_add(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_sub(instruction)):
        instruction_description, next_instruction_pos = execute_category2_sub(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_mul(instruction)):
        instruction_description, next_instruction_pos = execute_category2_mul(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_and(instruction)):
        instruction_description, next_instruction_pos = execute_category2_and(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_nor(instruction)):
        instruction_description, next_instruction_pos = execute_category2_nor(
            instruction, instruction_pos, cache, execute)
    elif (is_category2_SLT(instruction)):
        instruction_description, next_instruction_pos = execute_category2_SLT(
            instruction, instruction_pos, cache, execute)
    else:
        assert False, "没有匹配指令"

    if len(instruction_description) != 0:
        if execute:
            content.append(
                "--------------------\nCycle:" +
                str(circle) +
                " " +
                instruction_description)
        else:
            content.append(instruction_description)
            # 执行一条指令后，返回下一条指令的地址
    return next_instruction_pos

# ADD R1 R2 r3
# [[R2,R3],[R1]]
# 获得读写操作数


def get_read_write_operand(instruction, cache):

    if (is_category1_add(instruction)):
        return get_read_and_write_operand_category1_add(instruction)
    elif (is_category1_J(instruction)):
        return get_read_and_write_operand_category1_J(instruction)
    elif (is_category1_JR(instruction)):
        return get_read_and_write_operand_category1_JR(instruction)
    elif (is_category1_BEQ(instruction)):
        return get_read_and_write_operand_category1_BEQ(instruction)
    elif (is_category1_SLL(instruction)):
        return get_read_and_write_operand_category1_SLL(instruction)
    elif (is_category1_LW(instruction)):
        return get_read_and_write_operand_category1_LW(instruction, cache)
    elif (is_category1_mult(instruction)):
        return get_read_and_write_operand_category1_mult(instruction)
    elif (is_category1_BGTZ(instruction)):
        return get_read_and_write_operand_category1_BGTZ(instruction)
    elif (is_category1_sub(instruction)):
        return get_read_and_write_operand_category1_sub(instruction)
    elif (is_category1_SW(instruction)):
        return get_read_and_write_operand_category1_SW(instruction, cache)
    elif (is_category1_BLTZ(instruction)):
        return get_read_and_write_operand_category1_BLTZ(instruction)
    elif (is_break(instruction)):
        return get_read_and_write_operand_break(instruction)
    elif (is_category1_SRA(instruction)):
        return get_read_and_write_operand_category1_SRA(instruction)
    elif (is_category1_SRL(instruction)):
        return get_read_and_write_operand_category1_SRL(instruction)
    elif (is_category2_add(instruction)):
        return get_read_and_write_operand_category2_add(instruction)
    elif (is_category2_sub(instruction)):
        return get_read_and_write_operand_category2_sub(instruction)
    elif (is_category2_mul(instruction)):
        return get_read_and_write_operand_category2_mul(instruction)
    elif (is_category2_and(instruction)):
        return get_read_and_write_operand_category2_and(instruction)
    elif (is_category2_nor(instruction)):
        return get_read_and_write_operand_category2_nor(instruction)
    elif (is_category2_SLT(instruction)):
        return get_read_and_write_operand_category2_SLT(instruction)
    else:
        assert False, "没有匹配指令"
    return None


def finished(cache):

    e = cache['IF Unit:Executed Instruction']

    if len(e) == 1 and is_break(e[0][1]):
        return True
    else:
        return False


# [地址，二进制指令，是否是新指令，指令呆了几个轮次]
def get_instruction_pos(t):
    return t[0]


def execute_instruction_which_can_be_executed(
        instructions, init_pos, cache, content, circle):

    if (len(cache['Post-ALU Buffer']) >
            0 and old_instruction(cache['Post-ALU Buffer'][0])):
        instruction_pos = get_instruction_pos(cache['Post-ALU Buffer'][0])
        execute_one_instruction(
            instructions,
            instruction_pos,
            init_pos,
            cache,
            content,
            True,
            circle)
        cache['Post-ALU Buffer'] = []

    if (len(cache['Post-ALUB Buffer']) >
            0 and old_instruction(cache['Post-ALUB Buffer'][0])):
        instruction_pos = get_instruction_pos(cache['Post-ALUB Buffer'][0])
        execute_one_instruction(
            instructions,
            instruction_pos,
            init_pos,
            cache,
            content,
            True,
            circle)
        cache['Post-ALUB Buffer'] = []

    if(len(cache['Post-MEM Buffer']) > 0 and old_instruction(cache['Post-MEM Buffer'][0])):
        instruction_pos = get_instruction_pos(cache['Post-MEM Buffer'][0])
        execute_one_instruction(
            instructions,
            instruction_pos,
            init_pos,
            cache,
            content,
            True,
            circle)
        cache['Post-MEM Buffer'] = []

    return None


def is_if_unit(instruction):
    return is_category1_J(instruction) or is_category1_JR(instruction) or is_category1_BEQ(instruction) or is_category1_BLTZ(
        instruction) or is_nop(instruction) or is_break(instruction) or is_category1_BGTZ(instruction)


def read_intructions_to_pre_issue_buffer(
        instructions, instruction_pos, init_pos, cache):

    for i in range(2):
        if len(cache['Pre-Issue Buffer']) >= 4:
            break

        instruction = instructions[(instruction_pos - init_pos) // 4]
        if(is_if_unit(instruction)):
            if(is_nop(instruction) or is_break(instruction) or is_category1_J(instruction)):
                cache['IF Unit:Executed Instruction'].append(
                    [instruction_pos, instruction, True, 0])
            else:
                cache['IF Unit:Waiting Instruction'] = [
                    [instruction_pos, instruction, True, 0]]
            cache['stop_read_instruction'] = True
            return instruction_pos
        else:
            cache['Pre-Issue Buffer'].append([instruction_pos,
                                              instruction, True, 0])

        instruction_pos = instruction_pos + 4
    return instruction_pos

# 操作数


def write_operand(instruction, cache):
    return get_read_write_operand(instruction, cache)[1]


def read_operand(instruction, cache):
    return get_read_write_operand(instruction, cache)[0]


def conflict(pre_instruction, cur_instruction, cache):
    pre_write = write_operand(pre_instruction, cache)
    cur_read = read_operand(cur_instruction, cache)
    for cur_read_op in cur_read:
        if cur_read_op in pre_write:
            return True

    return False


def not_conflict_with_pre(instruction, cur_index, cache):

    for pre_ins in cache['IF Unit:Waiting Instruction']:
        if(conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['IF Unit:Executed Instruction']:
        if(conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['Pre-ALU Queue']:
        if(conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['Post-ALU Buffer']:
        if (conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['Pre-ALUB Queue']:
        if (conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['Post-ALUB Buffer']:
        if (conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['Pre-MEM Queue']:
        if (conflict(pre_ins[1], instruction, cache)):
            return False

    for pre_ins in cache['Post-MEM Buffer']:
        if (conflict(pre_ins[1], instruction, cache)):
            return False

    for i in range(cur_index):
        if(conflict(cache['Pre-Issue Buffer'][i][1], instruction, cache)):
            return False

    return True


def choose_queue(instruction, cache):
    if(is_category1_add(instruction) or is_category2_add(instruction) or is_category1_sub(instruction) or is_category2_sub(instruction)):
        return cache['Pre-ALU Queue']
    elif(is_category1_SRL(instruction) or is_category1_SLL(instruction)):
        return cache['Pre-ALUB Queue']
    elif (is_category1_SW(instruction) or is_category1_LW(instruction) or is_category1_SRA(instruction) or is_category1_mult(instruction)):
        return cache['Pre-MEM Queue']
    elif(is_category1_BGTZ(instruction) or is_category1_BLTZ(instruction)
         or is_break(instruction) or is_category1_J(instruction) or is_category1_BEQ(instruction)):
        return cache['IF Unit:Waiting Instruction:']
    else:
        assert False, "error"


def other_bq(instruction, cache):
    q = choose_queue(instruction, cache)

    all_q = [
        cache['Pre-ALU Queue'],
        cache['Post-ALU Buffer'],
        cache['Pre-ALUB Queue'],
        cache['Post-ALUB Buffer'],
        cache['Pre-MEM Queue'],
        cache['Post-MEM Buffer']]
    qq = []
    for t in all_q:
        if t is not q:
            qq.extend(t)
    return qq


def remove_index_of_lst(arr, index):
    return arr[:index] + arr[index + 1:]


def add_instruction2queue(add_queue_element, cache):
    cnt = 0
    for index in add_queue_element:
        pos_instruction_pair = cache['Pre-Issue Buffer'][index - cnt]
        q = choose_queue(pos_instruction_pair[1], cache)
        if (len(q) < 2):
            set_ins_new(pos_instruction_pair)
            set_not_in_pre_iss(pos_instruction_pair)
            q.append(pos_instruction_pair)
            cache['Pre-Issue Buffer'] = remove_index_of_lst(
                cache['Pre-Issue Buffer'], index - cnt)
            cnt = cnt + 1


def old_instruction(pos_ins_pair):
    return not pos_ins_pair[2]

    # 判断是否可以写入queue


def can2queue(ins, cache, remain_pre_issue):
    bq = other_bq(ins, cache)
    for pre_iss in remain_pre_issue:
        if(conflict(pre_iss, ins, cache)):
            return False

    for other in bq:
        if(conflict(other, ins, cache)):
            return False

    q = choose_queue(ins, cache)
    if q is not cache['Pre-MEM Queue']:
        new_q = []
        if q is cache['Pre-ALU Queue']:
            new_q.extend(cache['Pre-ALU Queue'])
            new_q.extend(cache['Post-ALU Buffer'])

        if q is cache['Pre-ALUB Queue']:
            new_q.extend(cache['Pre-ALUB Queue'])
            new_q.extend(cache['Post-ALUB Buffer'])

        if q is cache['Pre-MEM Queue']:
            new_q.extend(cache['Pre-MEM Queue'])
            new_q.extend(cache['Post-MEM Buffer'])

        for pre_ins in new_q:
            if conflict(pre_ins, ins, cache):
                return False
    return True


def pre_issue_buffer2queue(cache):
    remain_pre_issue = []
    for ins in cache['Pre-Issue Buffer']:
        if ins[2]:
            remain_pre_issue.append(ins)
            continue
        q = choose_queue(ins[1], cache)
        if(len(q) < 2 and can2queue(ins, cache, remain_pre_issue)):
            set_ins_new(ins)
            q.append(ins)
        else:
            remain_pre_issue.append(ins)
    cache['Pre-Issue Buffer'] = remain_pre_issue


def if_wait_unit_can_execute(cache):
    if(len(cache['IF Unit:Waiting Instruction']) == 0):
        return False

    other_ins = cache['Pre-Issue Buffer'] + cache['Pre-ALU Queue'] + cache['Post-ALU Buffer'] \
        + cache['Pre-ALUB Queue'] + cache['Post-ALUB Buffer'] + cache['Pre-MEM Queue'] \
        + cache['Post-MEM Buffer']

    cur_ins = cache['IF Unit:Waiting Instruction'][0]
    for ins in other_ins:
        if(conflict(ins[1], cur_ins[1], cache)):
            return False
    return True


def set_ins_old(pos_ins_pair):
    pos_ins_pair[2] = False
    return pos_ins_pair


def set_ins_new(pos_ins_pair):
    pos_ins_pair[2] = True
    return pos_ins_pair


def set_not_in_pre_iss(pos_instruction_pair):
    pos_instruction_pair[3] = 0
    return pos_instruction_pair


def if_unit2buffer(instructions, init_pos, cache, content, circle):
    if (len(cache['IF Unit:Waiting Instruction']) == 1):
        if (if_wait_unit_can_execute(cache) and old_instruction(
                cache['IF Unit:Waiting Instruction'][0])):
            cache['IF Unit:Executed Instruction'] = cache['IF Unit:Waiting Instruction']
            set_ins_new(cache['IF Unit:Executed Instruction'][0])
            cache['IF Unit:Waiting Instruction'] = []

# alub每次加一


def add_one_count2alub(cache):
    for ins in cache['Pre-ALUB Queue']:
        ins[3] = ins[3] + 1
    return cache


def queue2buffer(instructions, init_pos, cache, content, circle):
    if(len(cache['Pre-ALU Queue']) > 0 and old_instruction(cache['Pre-ALU Queue'][0])):
        cache['Post-ALU Buffer'] = [cache['Pre-ALU Queue'][0]]
        set_ins_new(cache['Post-ALU Buffer'][0])
        cache['Pre-ALU Queue'] = cache['Pre-ALU Queue'][1:]
    if(len(cache['Pre-ALUB Queue']) > 0 and old_instruction(cache['Pre-ALUB Queue'][0]) and cache['Pre-ALUB Queue'][0][3] > 1):
        cache['Post-ALUB Buffer'] = [cache['Pre-ALUB Queue'][0]]
        set_ins_new(cache['Post-ALUB Buffer'][0])

        cache['Pre-ALUB Queue'] = cache['Pre-ALUB Queue'][1:]

    remain_lst = []
    first = True
    # execute
    if (len(cache['Pre-MEM Queue']) > 0):
        ins = cache['Pre-MEM Queue'][0]
        if old_instruction(ins):
            if is_category1_SW(ins[1]):
                instruction_pos = get_instruction_pos(ins)
                execute_one_instruction(
                    instructions,
                    instruction_pos,
                    init_pos,
                    cache,
                    content,
                    True,
                    circle)
                remain_lst = cache['Pre-MEM Queue'][1:]
            else:
                if(len(cache['Post-MEM Buffer']) == 0):
                    cache['Post-MEM Buffer'] = [ins]
                    set_ins_new(ins)
                    remain_lst = cache['Pre-MEM Queue'][1:]
                else:
                    remain_lst = cache['Pre-MEM Queue']
        else:
            remain_lst = cache['Pre-MEM Queue']

    cache['Pre-MEM Queue'] = remain_lst

    return None


def set_all_ins_old(cache):
    all_ins = cache['IF Unit:Waiting Instruction'] + cache['IF Unit:Executed Instruction'] \
        + cache['Pre-Issue Buffer'] + cache['Pre-ALU Queue'] + cache['Post-ALU Buffer'] \
        + cache['Pre-ALUB Queue'] + cache['Post-ALUB Buffer'] + cache['Pre-MEM Queue'] + cache['Post-MEM Buffer']

    for ins in all_ins:
        set_ins_old(ins)
    return cache


def execute_if_unit(instructions, init_pos, cache, content, circle):
    # 有没有这条指令   并呆过一段时间
    if (len(cache['IF Unit:Executed Instruction']) > 0 and old_instruction(
            cache['IF Unit:Executed Instruction'][0])):
        instruction_pos = get_instruction_pos(
            cache['IF Unit:Executed Instruction'][0])
        next_pos = execute_one_instruction(
            instructions,
            instruction_pos,
            init_pos,
            cache,
            content,
            True,
            circle)
        cache['IF Unit:Executed Instruction'] = []
        cache['stop_read_instruction'] = False
        return next_pos


def execute_instructions(instructions, init_pos, cache, content, execute):
    ret = content

    instruction_pos = init_pos
    last_pos = init_pos + 4 * (len(instructions))
    data_address = get_data_address(instructions, init_pos)  # 获取数据地址
    cycle = 1
    read_pos = init_pos

    while (True):
        # 如果每个都有指令，先执行跳转语句
        change_pos = False  # 是否会改变位置，跳转就会改变位置
        # 一定要呆过一轮
        if (len(cache['IF Unit:Executed Instruction']) > 0 and old_instruction(
                cache['IF Unit:Executed Instruction'][0])):
            change_pos = True
        next_pos = execute_if_unit(instructions, init_pos, cache, [], cycle)
        if change_pos:
            read_pos = next_pos
            # 判断是否读到跳转指令，读到的话就停止再读
        if (not cache['stop_read_instruction']):
            read_pos = read_intructions_to_pre_issue_buffer(
                instructions, read_pos, init_pos, cache)

        # 从issue读到选择的buffer
        pre_issue_buffer2queue(cache)
        # IF Unit里wait 到 execute
        if_unit2buffer(instructions, init_pos, cache, [], cycle)
        # 返回下一个地址
        next_pos = execute_instruction_which_can_be_executed(
            instructions, init_pos, cache, content, cycle)
        queue2buffer(instructions, init_pos, cache, [], cycle)
        set_all_ins_old(cache)
        # 设置为旧的，证明执行过。所以要记录它执行过几个轮次
        add_one_count2alub(cache)
        ret.append(
            "--------------------\nCycle:" +
            str(cycle) +
            "\n\n" +
            cache_state(
                instructions,
                init_pos,
                cache))
        if(finished(cache)):
            break
        cycle += 1
    return ret


def split_instructions(instructions):
    index_of_break = -1
    for i in range(len(instructions)):
        if is_break(instructions[i]):
            index_of_break = i
    assert index_of_break != -1, "没有break语句"
    return instructions[:index_of_break + 1], instructions[index_of_break + 1:]


def disassemble(file_path):
    disassembly_txt_content = []
    instruction_start_pos = 64
    global MAX_WIDTH_OF_ADDRESS
    all_instructions = load_instructions_from_file(file_path)
    cache = {}
    MAX_WIDTH_OF_ADDRESS = get_max_width_of_address(
        all_instructions, instruction_start_pos)

    execute_instructions(
        all_instructions,
        instruction_start_pos,
        cache,
        disassembly_txt_content,
        False)
    return disassembly_txt_content


def simulate(file_path):
    global MAX_WIDTH_OF_ADDRESS
    global DATA_ADDRESS  # 数据开始的位置
    dsimulation_txt_content = []  # 初始化数组
    instruction_start_pos = 64
    all_instructions = load_instructions_from_file(file_path)
    # 执行指令   数据指令
    execute_instruction, data_instruction = split_instructions(
        all_instructions)
    MAX_WIDTH_OF_ADDRESS = get_max_width_of_address(
        all_instructions, instruction_start_pos)
    # 数据指令地址
    DATA_ADDRESS = get_data_address(all_instructions, instruction_start_pos)
    cache = init_cache(
        data_instruction,
        instruction_start_pos +
        len(execute_instruction) *
        4)
    # 初始化内存
    execute_instructions(
        all_instructions,
        instruction_start_pos,
        cache,
        dsimulation_txt_content,
        True)
    return dsimulation_txt_content


def save_lst_to_file(content, file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, 'w') as f:
        for i in range(len(content)):
            content[i] = content[i] + "\n"
        f.writelines(content)


def generate_simulate(src_path, dst_path):
    simulation_content = simulate(src_path)
    save_lst_to_file(simulation_content, dst_path)
    print("simulate finished successfully !")


if __name__ == '__main__':
    generate_simulate('./input/sample.txt', './output/simulation.txt')

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
    cache = {}
    # init Register
    for i in range(32):
        cache['R' + str(i)] = 0

    num_data = len(data_instruction)
    pos = data_start_pos
    for i in range(num_data):
        cache[pos] = binary_str2int(data_instruction[i])
        pos += 4
    cache['IF UNIT'] = []
    cache['Pre-Issue Buffer'] = []
    cache['Pre-ALU Queue'] = []
    cache['Post-ALU Buffer'] = []
    cache['Pre-ALUB Queue'] = []
    cache['Post-ALUB Buffer'] = []
    cache['Pre-MEM Queue'] = []
    cache['Post-MEM Buffer'] = []
    return cache


def split_instruction(instruction, len_arr):
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
            "\t" + str(instruction_pos) + "\tBREAK"
        # print(desc)
    return desc, next_pos


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
            "\t" + str(instruction_pos) + "\tNOP"
    return desc, next_pos


def is_category1_J(instruction):
    arr = split_instruction(instruction, [6, 26])
    return arr[0] == "000010"


def execute_category1_J(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 26])
    describe = ""
    if execute:
        next_pos = int(arr[1], 2) * 4
        describe = str(instruction_pos) + "\t" + "J #" + \
            str(next_pos) + "\n\n" + cache_state(cache) + "\n"
        # print(describe)
        return describe, next_pos
    else:
        next_pos = int(arr[1], 2) * 4
        describe = " ".join(format_binary_str(instruction)) + \
            "\t" + str(instruction_pos) + "\tJ\t#" + str(next_pos)
        return describe, instruction_pos + 4


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
        desc = str(instruction_pos) + "\t" + "J #" + \
            str(next_pos) + "\n\n" + cache_state(cache) + "\n"
    else:
        if (cache['Config_ca'] == 0):
            next_pos = temp
        else:
            next_pos = (temp // 2) * 2
        desc = " ".join(arr) + "\t" + str(instruction_pos) + \
            "\tJ\t#" + str(next_pos)
        next_pos = instruction_pos + 4
    return desc, next_pos


def format_binary_str(instruction):
    arr = [1, 5, 5, 5, 5, 5, 6]
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
        desc = str(instruction_pos) + "\t" + "BEQ " + rs + ", " + rt + \
            ", #" + str(target_offset) + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " BEQ\t" + rs + ", " + rt + ", #" + str(target_offset)
    return desc, next_pos


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
        desc = str(instruction_pos) + "\t" + "BGTZ " + rs + ", #" + \
            str(target_offset) + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + \
            str(instruction_pos) + "\tBGTZ\t" + rs + ", #" + str(target_offset)

    return desc, next_pos


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
        desc = str(instruction_pos) + "" + "BLTZ " + rs + ", #" + \
            str(target_offset) + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + \
            str(instruction_pos) + "\tBLTZ\t" + rs + ", #" + str(target_offset)
    return desc, next_pos


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
        discribe = str(instruction_pos) + "\t" + "ADD " + rd + \
            ", " + rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
    else:
        # 最长宽度加空格
        discribe = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + "\tADD\t" + rd + ", " + rs + ", " + rt
    return discribe, instruction_pos + 4


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
        discribe = str(instruction_pos) + "\t" + "SUB " + rd + \
            ", " + rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
    else:
        discribe = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + "\tSUB\t" + rd + ", " + rs + ", " + rt
    return discribe, instruction_pos + 4


def is_category1_mult(instruction):
    # 前六位
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    return arr[0] == "011100" and arr[-2] == "00000" and arr[-1] == "000010"


def execute_category1_mult(instruction, instruction_pos, cache, execute):
    arr = split_instruction(instruction, [6, 5, 5, 5, 5, 6])
    rs = get_R_name(arr[1])
    rt = get_R_name(arr[2])
    rd = get_R_name(arr[3])
    desc = ""
    if execute:
        cache[rd] = cache[rs] * cache[rt]
        desc = str(instruction_pos) + "\t" + "MUL " + rd + ", " + \
            rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " MUL " + rd + ", " + rs + ", " + rt

    return desc, instruction_pos + 4


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
        desc = str(instruction_pos) + "\t" + "LW " + rt + ", " + str(
            offset) + "(" + base_name + ")" + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + "\tLW\t" + rt + ", " + str(offset) + "(" + base_name + ")"
    return desc, instruction_pos + 4


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
        desc = str(instruction_pos) + "\t" + "SW " + rt + ", " + str(
            offset) + "(" + base_name + ")" + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + "\tSW\t" + rt + ", " + str(offset) + "(" + base_name + ")"

    return desc, instruction_pos + 4


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
        desc = str(instruction_pos) + "\t" + "SLL " + rd + ", " + \
            rt + ", #" + str(sa) + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + "\tSLL\t" + rd + ", " + rt + ", #" + str(sa)
    return desc, instruction_pos + 4


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
        desc = str(instruction_pos) + "\t" + "SRL " + rd + ", " + \
            rt + ", #" + str(sa) + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + "\tSRL\t" + rd + ", " + rt + ", #" + str(sa)
    return desc, instruction_pos + 4


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
        desc = str(instruction_pos) + "\t" + "SRA " + rd + ", " + \
            rt + ", #" + str(sa) + "\n\n" + cache_state(cache) + "\n"
    else:
        desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
            instruction_pos) + " SRA " + rd + ", " + rt + ", #" + str(sa)
    return desc, instruction_pos + 4


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
            desc = str(instruction_pos) + "\t" + "ADD " + rd + ", " + \
                rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tADD\t" + rd + ", " + rs + ", " + rt
        return desc, instruction_pos + 4
    else:
        arr = split_instruction(instruction, [1, 5, 5, 5, 16])
        rs = get_R_name(arr[2])
        rt = get_R_name(arr[3])
        immediate = binary_str2int(arr[4])
        if execute:
            cache[rt] = cache[rs] + immediate
            desc = str(instruction_pos) + "\t" + "ADD " + rt + ", " + rs + \
                ", #" + str(immediate) + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tADD\t" + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


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
            desc = str(instruction_pos) + "\t" + "SUB\t" + rd + ", " + \
                rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tSUB\t" + rd + ", " + rs + ", " + rt
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
                instruction_pos) + "\tSUB\t" + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


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
            desc = str(instruction_pos) + "\t" + "MUL " + rd + ", " + \
                rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tMUL\t" + rd + ", " + rs + ", " + rt
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
                instruction_pos) + "\tMUL\t" + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


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
            desc = str(instruction_pos) + "\t" + "AND " + rd + ", " + \
                rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tAND\t" + rd + ", " + rs + ", " + rt
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
                instruction_pos) + "\tAND\t" + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


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
            desc = str(instruction_pos) + "\t" + "NOR " + rd + ", " + \
                rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tNOR\t" + rd + ", " + rs + ", " + rt
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
                instruction_pos) + "\tNOR\t" + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


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
            desc = str(instruction_pos) + "\t" + "SLT " + rd + ", " + \
                rs + ", " + rt + "\n\n" + cache_state(cache) + "\n"
        else:
            desc = " ".join(format_binary_str(instruction)) + "\t" + format_address_with_width(
                instruction_pos) + "\tSLT\t" + rd + ", " + rs + ", " + rt
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
                instruction_pos) + "\tSLT\t" + rt + ", " + rs + ", #" + str(immediate)
        return desc, instruction_pos + 4


def execute_int(instructions, init_pos, instruction_pos, content):
    instruction = instructions[(instruction_pos - init_pos) // 4]

    num = binary_str2int(instruction)
    content.append(
        instruction +
        "\t" +
        format_address_with_width(instruction_pos) +
        "\t" +
        str(num))
    return instruction_pos + 4


def cache_state(cache):
    data_address = DATA_ADDRESS
    state = "Registers\n"

    R00 = "R00:"
    for i in range(16):
        R00 = R00 + '\t' + str(cache['R' + str(i)])

    R00 = R00 + "\n"
    state = state + R00

    R16 = "R16:"
    for i in range(16):
        R16 = R16 + "\t" + str(cache['R' + str(16 + i)])
    R16 = R16 + "\n\n"
    state = state + R16
    Data = "Data\n"
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
    # 下一条指令位置，即返回的东西
    # 是否执行，比如disma只翻译，不执行
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
    return next_instruction_pos


def execute_instructions(instructions, init_pos, cache, content, execute):
    instruction_pos = init_pos
    last_pos = init_pos + 4 * (len(instructions))

    data_address = get_data_address(instructions, init_pos)  # 获得数据（164那个位置）的地址
    circle = 1
    while (instruction_pos != data_address):
        instruction_pos = execute_one_instruction(
            instructions, instruction_pos, init_pos, cache, content, execute, circle)
        circle += 1

    if not execute:
        while (instruction_pos != last_pos):
            instruction_pos = execute_int(
                instructions, init_pos, instruction_pos, content)
    return None


def split_instructions(instructions):
    index_of_break = -1
    for i in range(len(instructions)):
        if is_break(instructions[i]):
            index_of_break = i

    assert index_of_break != -1, "没有break语句"

    return instructions[:index_of_break + 1], instructions[index_of_break + 1:]


def disassemble(file_path):
    disassembly_txt_content = []  # 一维数组，每一个字符串是一行
    instruction_start_pos = 64  # 指令开始位置
    global MAX_WIDTH_OF_ADDRESS  # 全局变量  地址最大宽度+1来保证对称
    all_instructions = load_instructions_from_file(file_path)  # 跳到这个函数读到所有指令了
    cache = {}  # 开了个字典，R0 对应寄存器为1 ，就会设置键值为1
    MAX_WIDTH_OF_ADDRESS = get_max_width_of_address(
        all_instructions, instruction_start_pos)
    # 全局变量  获得地址最大宽度+1来保证对称

    execute_instructions(
        all_instructions,
        instruction_start_pos,
        cache,
        disassembly_txt_content,
        False)
    return disassembly_txt_content


def simulate(file_path):
    global MAX_WIDTH_OF_ADDRESS
    global DATA_ADDRESS
    dsimulation_txt_content = []
    instruction_start_pos = 64
    all_instructions = load_instructions_from_file(file_path)
    execute_instruction, data_instruction = split_instructions(
        all_instructions)
    MAX_WIDTH_OF_ADDRESS = get_max_width_of_address(
        all_instructions, instruction_start_pos)
    DATA_ADDRESS = get_data_address(all_instructions, instruction_start_pos)
    cache = init_cache(
        data_instruction,
        instruction_start_pos +
        len(execute_instruction) *
        4)

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
            if i != len(content) - 1:
                content[i] = content[i] + "\n"
                pass
        f.writelines(content)


def generate_disassembly(src_path, dst_path):
    disassembly_content = disassemble(src_path)
    save_lst_to_file(disassembly_content, dst_path)
    print("disassembly finished successfully !")


if __name__ == '__main__':
    disassembly_content = disassemble('./input/sample2.txt')
    simulation_content = simulate('./input/sample2.txt')
    save_lst_to_file(disassembly_content, './output/disassembly2.txt')

    save_lst_to_file(simulation_content, './output/simulation2.txt')
    print("finished successfully")

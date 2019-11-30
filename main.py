#-*- coding:utf-8 _*-
import simulate_module
import disassembly_module


if __name__ == '__main__':
    simulate_module.generate_simulate('./input/sample.txt', './output/simulation.txt')
    disassembly_module.generate_disassembly('./input/sample.txt', './output/disassembly.txt')
    print("finished successfully !")
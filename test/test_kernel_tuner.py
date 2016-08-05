from __future__ import print_function

import numpy
from nose.tools import raises
from .context import *

import kernel_tuner.interface as kernel_tuner
import kernel_tuner.cuda as cuda
import kernel_tuner.opencl as opencl
from kernel_tuner.util import *


def test_get_grid_dimensions1():

    problem_size = (1024, 1024)

    params = dict()
    params["block_x"] = 41
    params["block_y"] = 37

    grid_div_x = ["block_x"]
    grid_div_y = ["block_y"]

    grid = get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

    assert len(grid) == 2
    assert isinstance(grid[0], int)
    assert isinstance(grid[1], int)

    print(grid)
    assert grid[0] == 25
    assert grid[1] == 28

    grid = get_grid_dimensions(problem_size, params,
                    None, grid_div_x)

    print(grid)
    assert grid[0] == 25
    assert grid[1] == 1024

    grid = get_grid_dimensions(problem_size, params,
                    grid_div_y, None)

    print(grid)
    assert grid[0] == 1024
    assert grid[1] == 28

def test_get_grid_dimensions2():

    problem_size = (1024, 1024)

    params = dict()
    params["block_x"] = 41
    params["block_y"] = 37

    grid_div_x = ["block_x*8"]
    grid_div_y = ["(block_y+2)/8"]

    grid = get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

    assert grid[0] == 4
    assert grid[1] == 256

def test_get_grid_dimensions3():

    problem_size = ("num_blocks_x", "num_blocks_y*3")

    params = dict()
    params["num_blocks_x"] = 71
    params["num_blocks_y"] = 57

    grid_div_x = []
    grid_div_y = []

    grid = get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

    assert grid[0] == 71
    assert grid[1] == 171

@raises(TypeError)
def test_get_grid_dimensions4():

    problem_size = (3.8, "num_blocks_y*3")

    params = dict()
    params["num_blocks_x"] = 71
    params["num_blocks_y"] = 57

    grid_div_x = []
    grid_div_y = []
    get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

def test_get_grid_dimensions5():

    problem_size = (1024, 1024)

    params = dict()
    params["block_x"] = 41
    params["block_y"] = 37

    grid_div_x = ["block_x", "block_y"]
    grid_div_y = ["(block_y+2)/8"]

    grid = get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

    print(grid)

    assert grid[0] == 1
    assert grid[1] == 256


def test_get_grid_dimensions6():

    problem_size = (numpy.int32(1024), numpy.int64(1024))

    params = dict()
    params["block_x"] = 41
    params["block_y"] = 37

    grid_div_x = ["block_x", "block_y"]
    grid_div_y = ["(block_y+2)/8"]

    grid = get_grid_dimensions(problem_size, params,
                    grid_div_y, grid_div_x)

    print(grid)

    assert grid[0] == 1
    assert grid[1] == 256



def test_get_thread_block_dimensions():

    params = dict()
    params["block_size_x"] = 123
    params["block_size_y"] = 257

    threads = get_thread_block_dimensions(params)
    assert len(threads) == 3
    assert isinstance(threads[0], int)
    assert isinstance(threads[1], int)
    assert isinstance(threads[2], int)

    assert threads[0] == 123
    assert threads[1] == 257
    assert threads[2] == 1

def test_prepare_kernel_string():
    kernel = "this is a weird kernel"
    params = dict()
    params["is"] = 8

    output = prepare_kernel_string(kernel, params, (3,7))
    expected = "#define is 8\n#define grid_size_y 7\n#define grid_size_x 3\nthis is a weird kernel"
    print(output)
    assert output == expected

def test_replace_param_occurrences():
    kernel = "this is a weird kernel"
    params = dict()
    params["is"] = 8
    params["weird"] = 14

    new_kernel = replace_param_occurrences(kernel, params)
    assert new_kernel == "th8 8 a 14 kernel"

    new_kernel = replace_param_occurrences(kernel, dict())
    assert kernel == new_kernel

    params = dict()
    params["blablabla"] = 8
    new_kernel = replace_param_occurrences(kernel, params)
    assert kernel == new_kernel

@raises(Exception)
def test_check_restrictions1():
    params = dict()
    params["a"] = 7
    params["b"] = 4
    params["c"] = 1
    restrictions = ["a==b+c"]
    check_restrictions(restrictions, params)
    assert False

def test_check_restrictions2():
    params = dict()
    params["a"] = 7
    params["b"] = 4
    params["c"] = 3
    restrictions = ["a==b+c", "b==b", "a-b==c"]
    #test that the call does not return an exception
    try:
        check_restrictions(restrictions, params)
        assert True
    except Exception:
        assert False

def test_detect_language1():
    lang = None
    kernel_string = "__global__ void vector_add( ... );"
    lang = detect_language(lang, kernel_string)
    assert lang == "CUDA"

def test_detect_language2():
    lang = None
    kernel_string = "__kernel void vector_add( ... );"
    lang = detect_language(lang, kernel_string)
    assert lang == "OpenCL"

def test_detect_language3():
    lang = None
    kernel_string = "blabla"
    lang = detect_language(lang, kernel_string)
    assert lang == "C"

def test_detect_language4():
    lang = "CUDA"
    kernel_string = "blabla"
    try:
        lang = detect_language(lang, kernel_string)
        assert lang == "CUDA"
    except Exception:
        assert False


def test_get_device_interface1():
    skip_if_no_cuda_device()
    lang = "CUDA"
    dev = get_device_interface(lang, 0, 0)
    assert isinstance(dev, cuda.CudaFunctions)

def test_get_device_interface2():
    skip_if_no_opencl()
    lang = "OpenCL"
    dev = get_device_interface(lang, 0, 0)
    assert isinstance(dev, opencl.OpenCLFunctions)

@raises(Exception)
def test_get_device_interface3():
    lang = "blabla"
    get_device_interface(lang, 0, 0)

def test_check_argument_list1():
    args = [numpy.int32(5), 'blah', numpy.array([1, 2, 3])]
    try:
        check_argument_list(args)
        print("Expected a TypeError to be raised")
        assert False
    except TypeError as e:
        print(str(e))
        assert "at position 1" in str(e)
    except Exception:
        print("Expected a TypeError to be raised")
        assert False

def test_check_argument_list2():
    args = [numpy.int32(5), numpy.float64(4.6), numpy.array([1, 2, 3])]
    check_argument_list(args)
    #test that no exception is raised
    assert True







#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行处理模块
"""

import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Callable, Any, Optional


class ParallelProcessor:
    """并行处理器"""
    def __init__(self, max_workers: Optional[int] = None, use_threads: bool = True):
        """初始化并行处理器
        
        Args:
            max_workers: 最大工作线程/进程数
            use_threads: 是否使用线程池（False则使用进程池）
        """
        self.max_workers = max_workers
        self.use_threads = use_threads
    
    def process(self, items: List[Any], func: Callable[[Any], Any]) -> List[Any]:
        """并行处理多个项目
        
        Args:
            items: 待处理的项目列表
            func: 处理函数
        
        Returns:
            处理结果列表
        """
        if not items:
            return []
        
        results = []
        
        try:
            # 选择执行器
            if self.use_threads:
                executor = ThreadPoolExecutor(max_workers=self.max_workers)
            else:
                executor = ProcessPoolExecutor(max_workers=self.max_workers)
            
            # 提交任务
            future_to_item = {executor.submit(func, item): item for item in items}
            
            # 收集结果
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logging.error(f"处理项目失败: {str(e)}")
        except Exception as e:
            logging.error(f"并行处理失败: {str(e)}")
            # 失败时使用串行处理
            for item in items:
                try:
                    result = func(item)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logging.error(f"串行处理项目失败: {str(e)}")
        
        return results
    
    def map(self, items: List[Any], func: Callable[[Any], Any]) -> List[Any]:
        """并行映射函数到多个项目
        
        Args:
            items: 待处理的项目列表
            func: 映射函数
        
        Returns:
            处理结果列表
        """
        return self.process(items, func)


def parallel_process(items: List[Any], func: Callable[[Any], Any], max_workers: Optional[int] = None, use_threads: bool = True) -> List[Any]:
    """并行处理多个项目的便捷函数
    
    Args:
        items: 待处理的项目列表
        func: 处理函数
        max_workers: 最大工作线程/进程数
        use_threads: 是否使用线程池（False则使用进程池）
    
    Returns:
        处理结果列表
    """
    processor = ParallelProcessor(max_workers=max_workers, use_threads=use_threads)
    return processor.process(items, func)


def parallel_map(items: List[Any], func: Callable[[Any], Any], max_workers: Optional[int] = None, use_threads: bool = True) -> List[Any]:
    """并行映射函数到多个项目的便捷函数
    
    Args:
        items: 待处理的项目列表
        func: 映射函数
        max_workers: 最大工作线程/进程数
        use_threads: 是否使用线程池（False则使用进程池）
    
    Returns:
        处理结果列表
    """
    return parallel_process(items, func, max_workers=max_workers, use_threads=use_threads)

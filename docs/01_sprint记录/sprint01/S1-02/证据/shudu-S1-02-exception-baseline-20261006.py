import copy
import json
import os
import sys
from collections import Counter
from contextlib import ExitStack
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
import conftest
import shudu.logic_solver._engine as engine
import shudu.logic_solver._project as project
from shudu.sudoku_hints import pending_step

board = [[0] * 9 for _ in range(9)]
notes = {}
before = copy.deepcopy((board, notes))
counts = Counter()
shapes = set()

def tracked(label, original):
    def call(*args, **kwargs):
        counts[label] += 1
        for value in args:
            if hasattr(value, 'shape'):
                shapes.add(tuple(value.shape))
        return original(*args, **kwargs)
    return call

def fail_finder(*args):
    raise RuntimeError('baseline_probe_exception')

fields = ['candidate_sets', 'masks_from_board', 'apply_placement',
          'find_hidden_single', 'find_naked_single', 'find_naked_pair',
          'find_hidden_pair', 'find_naked_triple', 'find_hidden_triple',
          'find_pointing_pair', 'find_box_line', 'find_x_wing', 'find_xy_wing']
with ExitStack() as stack:
    for attr in fields:
        original = fail_finder if attr == 'find_hidden_single' else getattr(engine, attr)
        stack.enter_context(patch.object(engine, attr, tracked(attr, original)))
    stack.enter_context(patch.object(project, 'capture_candidates', tracked('capture_candidates', project.capture_candidates)))
    stack.enter_context(patch.object(engine.NumbaLogicSolver, '_hidden_single_sources', tracked('base_hidden_single_evidence', engine.NumbaLogicSolver._hidden_single_sources)))
    stack.enter_context(patch.object(project.ShuduSolver, '_hidden_single_evidence', tracked('project_hidden_single_evidence', project.ShuduSolver._hidden_single_evidence)))
    stack.enter_context(patch.object(project.ShuduSolver, 'next_step', tracked('next_step', project.ShuduSolver.next_step)))
    try:
        pending_step(board, notes)
    except RuntimeError as error:
        assert str(error) == 'baseline_probe_exception'
        outcome = {'exception_type': type(error).__name__, 'message': str(error)}
    else:
        raise AssertionError('Injected original exception did not propagate')
assert (board, notes) == before
print(json.dumps({'scenario': 'hint_exception_fixed_empty_board',
                  'fixture': {'board': board, 'notes': [], 'shape': [9, 9]},
                  'injection': 'engine.find_hidden_single raises RuntimeError before mutation',
                  'calls': {field: counts[field] for field in fields + ['capture_candidates', 'base_hidden_single_evidence', 'project_hidden_single_evidence', 'next_step']},
                  'array_shapes': sorted(shapes), 'outcome': outcome,
                  'inputs_unchanged': True, 'measurement': 'call_counts_and_input_shapes'}, indent=2))

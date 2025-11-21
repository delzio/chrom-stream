import pytest
import os
import pandas as pd

from batch_context.batch_context_generator import BatchContextGenerator

def test_phases_exist(good_batch_context_with_holds, good_batch_context_no_holds, bad_batch_context_with_holds, bad_batch_context_no_holds):
    for bc in [good_batch_context_with_holds, good_batch_context_no_holds,
                          bad_batch_context_with_holds, bad_batch_context_no_holds]:
        assert "phase" in bc.phase_data.columns
        assert bc.phase_data["phase"].nunique() > 0

def test_phase_counts_match(good_batch_context_with_holds, good_batch_context_no_holds, bad_batch_context_with_holds, bad_batch_context_no_holds):
    counts = []
    for bc in [good_batch_context_with_holds, good_batch_context_no_holds,
                bad_batch_context_with_holds, bad_batch_context_no_holds]:
        counts.append(bc.phase_data["phase"].nunique())

    assert len(set(counts)) == 1

def test_batches_with_holds_phases_consistent(good_batch_context_with_holds, bad_batch_context_with_holds):
    gbc_phases = good_batch_context_with_holds.phase_data
    bbc_phases = bad_batch_context_with_holds.phase_data
    assert gbc_phases.equals(bbc_phases)

def test_batches_no_holds_phases_consistent(good_batch_context_no_holds, bad_batch_context_no_holds):
    gbc_phases = good_batch_context_no_holds.phase_data
    bbc_phases = bad_batch_context_no_holds.phase_data
    assert gbc_phases.equals(bbc_phases)



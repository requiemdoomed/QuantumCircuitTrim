"""Execute every notebook cell; optionally use an in-process kernel."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def working_directory(path):
    before = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(before)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-process', action='store_true', help='Avoid local socket requirements')
    parser.add_argument('--save', action='store_true', help='Save fresh notebook outputs')
    args = parser.parse_args()
    path = ROOT / 'notebooks' / 'CircuitTrim.ipynb'
    notebook = nbformat.read(path,as_version=4)
    nbformat.validate(notebook)
    if args.in_process:
        from ipykernel.inprocess.manager import InProcessKernelManager
        from IPython.utils.capture import capture_output
        manager = InProcessKernelManager()
        manager.start_kernel()
        try:
            with working_directory(path.parent):
                count = 0
                for cell in notebook.cells:
                    if cell.cell_type != 'code':
                        continue
                    count += 1
                    with capture_output() as captured:
                        result = manager.kernel.shell.run_cell(cell.source)
                    if result.error_before_exec or result.error_in_exec:
                        raise RuntimeError(f'Notebook code cell {count} failed: {result.error_before_exec or result.error_in_exec}')
                    cell.execution_count = count
                    cell.outputs = []
                    if captured.stdout:
                        cell.outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
                    if captured.stderr:
                        cell.outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
                    for output in captured.outputs:
                        cell.outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
                workbench = manager.kernel.shell.user_ns.get('workbench')
                if workbench:
                    if workbench.result is None:
                        raise AssertionError('The initial workbench run failed.')
                    workbench.close()
        finally:
            manager.shutdown_kernel()
    else:
        from nbclient import NotebookClient
        NotebookClient(notebook,timeout=180,kernel_name='python3',
                       resources={'metadata':{'path':str(path.parent)}}).execute()
    count = sum(cell.cell_type == 'code' for cell in notebook.cells)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            assert all(output.output_type != 'error' for output in cell.outputs)
            # Keeping a stable preview while loading live widgets on execution.
            if 'workbench = launch()' in cell.source:
                cell.outputs = [nbformat.v4.new_output('stream',name='stdout',
                                text='Run this cell to open the interactive workbench.\n')]
    if args.save:
        nbformat.write(notebook,path)
    print(f'Passed: {count} notebook code cells.')


if __name__ == '__main__':
    main()

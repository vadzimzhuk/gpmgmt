import unittest
from my_app.workflow import Workflow

class TestWorkflow(unittest.TestCase):
    def test_workflow_name(self):
        wf = Workflow(name="demo")
        self.assertEqual(wf.name, "demo")

    def test_workflow_runs(self):
        wf = Workflow(name="demo")
        result = wf.run()
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
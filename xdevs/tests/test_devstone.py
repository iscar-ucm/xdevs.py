import unittest
from xdevs import INFINITY
from xdevs.sim import Coordinator
from xdevs.examples.devstone.devstone import DEVStone, LI, HI, HO, HOmod
import random


class DevstoneUtilsTestCase(unittest.TestCase):

    def __init__(self, name, num_valid_params_sets: int = 10):
        super().__init__(name)
        self.valid_high_params = []
        self.valid_low_params = []

        for _ in range(int(num_valid_params_sets)):
            self.valid_high_params.append([random.randint(1, 100), random.randint(1, 200), 0, 0])

        for _ in range(int(num_valid_params_sets)):
            self.valid_low_params.append([random.randint(1, 20), random.randint(1, 30), 0, 0])

    def check_invalid_inputs(self, base_class):
        self.assertRaises(ValueError, base_class, "root", 0, 1, 1, 1)
        self.assertRaises(ValueError, base_class, "root", 1, 0, 1, 1)
        self.assertRaises(ValueError, base_class, "root", 1, 1, -1, 0)
        self.assertRaises(ValueError, base_class, "root", 1, 1, 0, -1)
        self.assertRaises(ValueError, base_class, "root", 0, 1, -1, -1)
        self.assertRaises(ValueError, base_class, "root", 0, 0, -1, -1)


class TestLI(DevstoneUtilsTestCase):

    def test_structure(self):
        """
        Check structure params: atomic modules, ic's, eic's and eoc's.
        """
        for params_tuple in self.valid_high_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "LI"
            params["test"] = True

            with self.subTest(**params):
                self._check_structure(**params)

    def test_structure_corner_cases(self):
        params = {"depth": 10, "width": 1, "int_delay": 1, "ext_delay": 1, "test": True, "model_type": "LI"}
        self._check_structure(**params)
        params["depth"] = 1
        self._check_structure(**params)

    def _check_structure(self, **params):
        root = DEVStone("LI_root", **params)
        self.assertEqual(root.n_atomics, (params["width"] - 1) * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eics, params["width"] * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eocs, params["depth"])
        self.assertEqual(root.n_ics, 0)

    def test_behavior(self):
        """
        Check behaviour params: number of int and ext transitions.
        """
        for params_tuple in self.valid_low_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "LI"
            params["test"] = True
            with self.subTest(**params):
                root = DEVStone("LI_root", **params)
                coord = Coordinator(root)
                coord.initialize()
                # coord.inject(li_root.i_in, 0)
                coord.simulate_time(INFINITY)

                self.assertEqual(root.n_internals, (params["width"] - 1) * (params["depth"] - 1) + 1)
                self.assertEqual(root.n_externals, (params["width"] - 1) * (params["depth"] - 1) + 1)
                self.assertEqual(root.n_events, (params["width"] - 1) * (params["depth"] - 1) + 1)

    def test_invalid_inputs(self):
        super().check_invalid_inputs(LI)


class TestHI(DevstoneUtilsTestCase):

    def test_structure(self):
        """
        Check structure params: atomic modules, ic's, eic's and eoc's.
        """
        for params_tuple in self.valid_high_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "HI"
            params["test"] = True

            with self.subTest(**params):
                self._check_structure(**params)

    def test_structure_corner_cases(self):
        params = {"depth": 10, "width": 1, "int_delay": 1, "ext_delay": 1, "model_type": "HI"}
        self._check_structure(**params)
        params["depth"] = 1
        self._check_structure(**params)

    def _check_structure(self, **params):
        root = DEVStone("HI_root", **params)
        self.assertEqual(root.n_atomics, (params["width"] - 1) * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eics, params["width"] * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eocs, params["depth"])
        self.assertEqual(root.n_ics, (params["width"] - 2) * (params["depth"] - 1) if params["width"] > 2 else 0)

    def test_behavior(self):
        """
        Check behaviour params: number of int and ext transitions.
        """
        for params_tuple in self.valid_low_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "HI"
            params["test"] = True

            with self.subTest(**params):
                root = DEVStone("HI_root", **params)
                coord = Coordinator(root)
                coord.initialize()
                coord.simulate_time(INFINITY)

                self.assertEqual(root.n_internals, (((params["width"] - 1) * params["width"]) / 2) * (params["depth"] - 1) + 1)
                self.assertEqual(root.n_externals, (((params["width"] - 1) * params["width"]) / 2) * (params["depth"] - 1) + 1)
                self.assertEqual(root.n_events, (((params["width"] - 1) * params["width"]) / 2) * (params["depth"] - 1) + 1)

    def test_invalid_inputs(self):
        super().check_invalid_inputs(HI)


class TestHO(DevstoneUtilsTestCase):

    def test_structure(self):
        """
        Check structure params: atomic modules, ic's, eic's and eoc's.
        """
        for params_tuple in self.valid_high_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "HO"
            with self.subTest(**params):
                self._check_structure(**params)

    def test_structure_corner_cases(self):
        params = {"depth": 10, "width": 1, "int_delay": 1, "ext_delay": 1, "model_type": "HO"}
        self._check_structure(**params)
        params["depth"] = 1
        self._check_structure(**params)

    def _check_structure(self, **params):
        root = DEVStone("HO_root", **params)
        self.assertEqual(root.n_atomics, (params["width"] - 1) * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eics, (params["width"] + 1) * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eocs, params["width"] * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_ics, (params["width"] - 2) * (params["depth"] - 1) if params["width"] > 2 else 0)

    def test_behavior(self):
        """
        Check behaviour params: number of int and ext transitions.
        """
        for params_tuple in self.valid_low_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "HO"
            params["test"] = True

            with self.subTest(**params):
                root = DEVStone("HO_root", **params)
                coord = Coordinator(root)
                coord.initialize()
                # TODO aqui n_externals debería ser igual a n_atomics (pero no lo es...)
                coord.simulate_time(INFINITY)

                self.assertEqual(root.n_internals, (params["width"] - 1) * params["width"] / 2 * (params["depth"] - 1) + 1)
                self.assertEqual(root.n_externals, (params["width"] - 1) * params["width"] / 2 * (params["depth"] - 1) + 1)
                self.assertEqual(root.n_events, (params["width"] - 1) * params["width"] / 2 * (params["depth"] - 1) + 1)

    def test_invalid_inputs(self):
        super().check_invalid_inputs(HO)


class TestHOmod(DevstoneUtilsTestCase):
    def test_structure(self):
        """
        Check structure params: atomic modules, ic's, eic's and eoc's.
        """
        for params_tuple in self.valid_low_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "HOmod"

            with self.subTest(**params):
                self._check_structure(**params)

    def test_structure_corner_cases(self):
        params = {"depth": 10, "width": 1, "int_delay": 1, "ext_delay": 1, "model_type": "HOmod"}
        self._check_structure(**params)
        params["depth"] = 1
        self._check_structure(**params)

    def _check_structure(self, **params):
        root = DEVStone("HOmod_root", **params)
        self.assertEqual(root.n_atomics, ((params["width"] - 1) + ((params["width"] - 1) * params["width"]) / 2) * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eics, (2*(params["width"] - 1) + 1) * (params["depth"] - 1) + 1)
        self.assertEqual(root.n_eocs, params["depth"])
        # ICs relative to the "triangular" section
        exp_ic = (((params["width"] - 2) * (params["width"] - 1)) / 2) if params["width"] > 1 else 0
        # Plus the ones relative to the connection from the 2nd to 1st row...
        exp_ic += (params["width"] - 1) ** 2
        # ...and from the 1st to the couple component
        exp_ic += params["width"] - 1
        # Multiplied by the number of layers (except the deepest one, that doesn't have ICs)
        exp_ic *= (params["depth"] - 1)
        self.assertEqual(root.n_ics, exp_ic)

    def test_behavior(self):
        """
        Check behaviour params: number of int and ext transitions.
        """
        for params_tuple in self.valid_low_params:
            params = dict(zip(("depth", "width", "int_delay", "ext_delay"), params_tuple))
            params["model_type"] = "HOmod"
            params["test"] = True

            with self.subTest(**params):
                root = DEVStone("HOmod_root", **params)
                coord = Coordinator(root)
                coord.initialize()
                coord.simulate_time(INFINITY)

                calc_in = lambda x, w: 1 + (x - 1)*(w - 1)
                exp_trans = 1
                tr_atomics = sum(range(1, params["width"]))
                for i in range(1, params["depth"]):
                    num_inputs = calc_in(i, params["width"])
                    trans_first_row = (params["width"] - 1) * (num_inputs + params["width"] - 1)
                    exp_trans += num_inputs * tr_atomics + trans_first_row
                self.assertEqual(root.n_internals, exp_trans)
                self.assertEqual(root.n_externals, exp_trans)

                n = 1
                if params["width"] > 1 and params["depth"] > 1:
                    n += 2 * (params["width"] - 1)
                    aux = 0
                    for i in range(2, params["depth"]):
                        aux += 1 + (i - 1) * (params["width"] - 1)
                    n += aux * 2 * (params["width"] - 1) * (params["width"] - 1)
                    n += (aux + 1) * ((params["width"] - 1) * (params["width"] - 1) + (params["width"] - 2) * (params["width"] - 1) / 2)
                self.assertEqual(root.n_events, n)

    def test_invalid_inputs(self):
        super().check_invalid_inputs(HOmod)


if __name__ == '__main__':
    import unittest
    unittest.main()

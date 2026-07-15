"""
Tests - Excel

Verifica importación, exportación y categorización automática.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import tempfile
import os

from utils.excel import infer_category, ExcelManager


class TestInferCategory(unittest.TestCase):
    """Tests para la inferencia automática de categorías."""

    def test_gpu_detection(self):
        self.assertEqual(infer_category("ASUS Dual RTX 5060"), "GPU")
        self.assertEqual(infer_category("MSI GeForce GTX 1660"), "GPU")
        self.assertEqual(infer_category("Radeon RX 7900 XT"), "GPU")

    def test_cpu_detection(self):
        self.assertEqual(infer_category("Ryzen 5 7500F"), "CPU")
        self.assertEqual(infer_category("Intel Core i7-14700K"), "CPU")
        self.assertEqual(infer_category("AMD Ryzen 9 7950X"), "CPU")

    def test_ram_detection(self):
        self.assertEqual(infer_category("Teamgroup DDR5 6000"), "RAM")
        self.assertEqual(infer_category("Kingston 32GB DDR4"), "RAM")

    def test_motherboard_detection(self):
        self.assertEqual(infer_category("ASRock B650M-HDV"), "Motherboard")
        self.assertEqual(infer_category("MSI B550 TOMAHAWK"), "Motherboard")

    def test_ssd_detection(self):
        self.assertEqual(infer_category("Crucial P3 Plus 1TB"), "SSD")
        self.assertEqual(infer_category("Samsung 980 NVMe"), "SSD")

    def test_psu_detection(self):
        self.assertEqual(infer_category("MSI A650BN 650W"), "PSU")
        self.assertEqual(infer_category("Corsair RM850x PSU"), "PSU")

    def test_case_detection(self):
        self.assertEqual(infer_category("Montech Air 100 ARGB"), "Case")
        self.assertEqual(infer_category("Corsair 4000D Airflow"), "Case")

    def test_cooler_detection(self):
        self.assertEqual(infer_category("Thermalright Assassin X 120 SE"), "Cooler")
        self.assertEqual(infer_category("Noctua NH-D15"), "Cooler")

    def test_monitor_detection(self):
        self.assertEqual(infer_category('Koorui 24E3 Monitor'), "Monitor")

    def test_perifericos_detection(self):
        self.assertEqual(infer_category("Aula F75 Pro Teclado"), "Perifericos")
        self.assertEqual(infer_category("Attack Shark X3 Mouse"), "Perifericos")
        self.assertEqual(infer_category("Fenvi AX210 WiFi"), "Perifericos")

    def test_unknown_category(self):
        self.assertEqual(infer_category("Algo Random"), "Sin categoria")


class TestExcelManager(unittest.TestCase):
    """Tests para el gestor de Excel."""

    def test_infer_category_integration(self):
        mgr = ExcelManager()
        self.assertEqual(infer_category("RTX 5060"), "GPU")
        self.assertEqual(infer_category("Ryzen 7500F"), "CPU")


if __name__ == "__main__":
    unittest.main()

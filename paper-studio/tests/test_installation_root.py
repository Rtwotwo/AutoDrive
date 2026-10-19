import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import desktop


class InstallationRootTests(unittest.TestCase):
    def test_override_cannot_use_sibling_inside_enclosing_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp)/'repo';repo.mkdir();(repo/'.git').mkdir()
            source=repo/'paper-studio';source.mkdir()
            with patch('desktop.ROOT',source), patch.dict(os.environ,{'PAPER_STUDIO_HOME':str(repo/'private-runtime')}):
                with self.assertRaises(ValueError):desktop.installation_root()

    def test_fresh_source_uses_local_app_data_without_local_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(desktop,'ROOT',root/'checkout'),patch.dict(os.environ,{'LOCALAPPDATA':str(root/'private'),'PAPER_STUDIO_HOME':''}):
                self.assertEqual(desktop.installation_root(),(root/'private/PaperStudio').resolve())

    def test_private_override_and_checkout_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'checkout/.git').mkdir(parents=True)
            with patch.object(desktop,'ROOT',root/'checkout'),patch.dict(os.environ,{'PAPER_STUDIO_HOME':str(root/'private')}):
                self.assertEqual(desktop.installation_root(),(root/'private').resolve())
                os.environ['PAPER_STUDIO_HOME']=str(root/'checkout/data')
                with self.assertRaises(ValueError):desktop.installation_root()

    def test_outer_dotfiles_repo_does_not_expand_checkout_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'.git').mkdir()
            repo=root/'project';(repo/'.git').mkdir(parents=True)
            source=repo/'paper-studio';source.mkdir()
            with patch.object(desktop,'ROOT',source),patch.dict(os.environ,{'PAPER_STUDIO_HOME':str(root/'private')}):
                self.assertEqual(desktop.installation_root(),(root/'private').resolve())
                os.environ['PAPER_STUDIO_HOME']=str(repo/'runtime')
                with self.assertRaises(ValueError):desktop.installation_root()
                os.environ['PAPER_STUDIO_HOME']='relative'
                with self.assertRaises(ValueError):desktop.installation_root()


if __name__=='__main__':unittest.main()

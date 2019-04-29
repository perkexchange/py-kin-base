from unittest import TestCase
from pytest import raises

from kin_base.keypair import Keypair
from kin_base.exceptions import MissingSigningKeyError, NotValidParamError


def test_sep0005():
    # https://github.com/stellar/stellar-protocol/blob/master/ecosystem/sep-0005.md
    mnemonic = 'illness spike retreat truth genius clock brain pass fit cave bargain toe'
    seed = Keypair.deterministic(mnemonic).seed()
    assert seed == b'SDBKOVHBX2UFDTSEESHEEHR76OMJ5GMOWISBDC7BQOSF7FA2E23JRZLS'
    address = Keypair.deterministic(mnemonic, index=6).address().decode()
    assert address == 'GB37PRJSTEGB6CWTRU7DCSJWD4A22IYTGSHFEN73IJ3AM3CETFAZPRJO'

    mnemonic = 'cable spray genius state float twenty onion head street palace net private method loan turn phrase state blanket interest dry amazing dress blast tube'
    seed = Keypair.deterministic(mnemonic, passphrase='p4ssphr4se').seed()
    assert seed == b'SBRC5DWN6RPRY5IJABDVEUESPJBMQEIA5HNKEMERYUOKJ5VUCIXTSF6J'
    address = Keypair.deterministic(
        mnemonic, passphrase='p4ssphr4se', index=9).address().decode()
    assert address == 'GDPJJCIKGNOM73NXVYX5R76PNATGDP7IW4TWSOY5HOARGKZY2ZSBTVEA'

    mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
    seed = Keypair.deterministic(mnemonic).seed()
    assert seed == b'SDRX36LJA7O4S5GZ3PF7CCLO5S5XEXO6SAV7SFCHRCQHAASE2HOJY6TX'
    address = Keypair.deterministic(mnemonic, index=8).address().decode()
    assert address == 'GCAZEAOQBCGBJKH7OKJO35NIHAVGNP3A5NN2MUNB37Z4MI35AIC7K5PC'


class KeypairTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mnemonic = ('illness spike retreat truth genius clock brain pass '
                        'fit cave bargain toe')
        cls.keypair0 = Keypair.deterministic(cls.mnemonic)

    def test_from_seed(self):
        keypair = Keypair.from_seed(self.keypair0.seed())
        assert self.keypair0.address() == keypair.address()

    def test_sign_missing_signing_key_raise(self):
        keypair = Keypair.from_address(self.keypair0.address())
        raises(MissingSigningKeyError, keypair.sign, "")

    def test_init_wrong_type_key_raise(self):
        raises(NotValidParamError, Keypair, self.mnemonic)

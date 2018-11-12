# coding: utf-8
import pytest
from kin_base.memo import *
from kin_base.operation import *
from kin_base.transaction import Transaction
from kin_base.keypair import Keypair
from kin_base.transaction_envelope import TransactionEnvelope as Te


class TestTx:
    source = 'GDJVFDG5OCW5PYWHB64MGTHGFF57DRRJEDUEFDEL2SLNIOONHYJWHA3Z'
    seed = 'SAHPFH5CXKRMFDXEIHO6QATHJCX6PREBLCSFKYXTTCDDV6FJ3FXX4POT'
    dest = 'GCW24FUIFPC2767SOU4JI3JEAXIHYJFIJLH7GBZ2AVCBVP32SJAI53F5'

    def test_init_raise_redundant_argument(self):
        pytest.raises(
            TypeError, Transaction, self.source, dummy=[], sequence=1)

    def test_init_raise_account_code_wrong(self):
        pytest.raises(Exception, Transaction, self.source + "1", sequence=1)

    def do(self, network, opts):
        tx = Transaction(self.source, **opts)
        tx.add_operation(Inflation())
        envelope = Te(tx, network_id=network)
        signer = Keypair.from_seed(self.seed)
        envelope.sign(signer)
        envelope_b64 = envelope.xdr()
        print(envelope_b64)
        return envelope_b64

    def test_textMemo_ascii(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAEAAAAHdGVzdGluZwAAAAABAAAAAAAAAAkAAAAAAAAAAc0+E2MAAABAMQFOqFSB22TugUKMAyF+ReoaNe1eXUeuLgxbJ2fo/FqqSs13aszSTveEpOp+FXdYPWKnFREb6UO8lohSE5JaCQ=='
        assert (result == self.do(setup.network, {
            'sequence': 1,
            'memo': TextMemo('testing'),
        }))

    def test_textMemo_unicode(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAEAAAAMdMSTxaF0xKvFhsSjAAAAAQAAAAAAAAAJAAAAAAAAAAHNPhNjAAAAQPbTvBNXbVRC2yLA8BFVBB1IvgIlNykIn9heLQC709Mtq1OBOj222zrF0y07Hbe90iWtjAU98bGBQVSpf8GRUQk='
        assert (result == self.do(setup.network, {
            'sequence': 1,
            'memo': TextMemo('tēštīņģ'),
        }))

    def test_imprecise_fee(self, setup):
        with pytest.raises(NotValidParamError):
            self.do(setup.network, {
                'sequence': 1,
                'memo': TextMemo('testing'),
                'fee': 100.54
            })


class TestMultiOp:
    address = 'GDJVFDG5OCW5PYWHB64MGTHGFF57DRRJEDUEFDEL2SLNIOONHYJWHA3Z'
    seed = 'SAHPFH5CXKRMFDXEIHO6QATHJCX6PREBLCSFKYXTTCDDV6FJ3FXX4POT'
    accounts = [
        {
            'address':
            'GCKMUHUBYSJNEIPMJ2ZHSXGSI7LLROFM5U43SWMRDV7J23HI63M7RW2D',
            'seed': 'SDKGBZFUZZEP3QKAFNLEINQ2MPD5QZJ35ZV7YNS6XCQ4NEHI6ND3ZMWC',
        },
        {
            'address':
            'GBG2TM6PGHAWRBVS37MBGOCQ7H7QQH7N2Y2WVUY7IMCEJ6MSF7LWQNIP',
            'seed': 'SAMM4N3BI447BUSTHPGO5NRHQY2J5QWECMPVHLXHZ3UKENU52UJ7MJLQ',
        },
        {
            'address':
            'GCQEAE6KDHPQMO3AJBRPSFV6FAPFYP27Q3EGE4PY4MZCTIV5RRA3KDBS',
            'seed': 'SDWJCTX6T3NJ6HEPDWFPMP33M2UDBPFKUCN7BIRFQYKXQTLO7NGDEVZE',
        },
    ]
    amount = "20"

    def make_envelope(self, *args, **kwargs):
        opts = {'sequence': 1, 'fee': 100 * len(args)}
        for opt, value in kwargs.items():
            opts[opt] = value
        tx = Transaction(self.address, **opts)
        for count, op in enumerate(args):
            tx.add_operation(op)
        envelope = Te(tx, network_id="TESTNET")
        signer = Keypair.from_seed(self.seed)
        envelope.sign(signer)
        envelope_b64 = envelope.xdr()
        print(envelope_b64)
        return envelope_b64

    def test_double_create_account(self):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAyAAAAAAAAAACAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAAAAAMNQAAAAAAAAAAAAAAAAE2ps88xwWiGst/YEzhQ+f8IH+3WNWrTH0MERPmSL9doAAAAAAAGGoAAAAAAAAAAAc0+E2MAAABA2zdnlvswhOeo+6memXxv9p9hBJCRhWW2UnhWQe7jKZDvvXBmz9A3hyXXu8eW0nBpkfglGM8ZAk1yzsajSrkXAw=='
        assert (result == self.make_envelope(
            CreateAccount(
                destination=self.accounts[0]['address'],
                starting_balance=self.amount,
            ),
            CreateAccount(
                destination=self.accounts[1]['address'],
                starting_balance="40",
            ),
        ))

    def test_double_payment(self):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAyAAAAAAAAAACAAAAAAAAAAAAAAACAAAAAAAAAAEAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAAAAAAAAAADDUAAAAAAAAAAAQAAAABNqbPPMcFohrLf2BM4UPn/CB/t1jVq0x9DBET5ki/XaAAAAAAAAAAAAAYagAAAAAAAAAABzT4TYwAAAEBvkDtGqFMIKFp4OsHU2InHITr+ret/gyoB2h3Qjls4MdPGg4aV5Gy5zVuL0xZirO6cemLaF+bWwDx0c4eAOIEK'
        assert (result == self.make_envelope(
            Payment(
                destination=self.accounts[0]['address'],
                asset=Asset.native(),
                amount=self.amount,
            ),
            Payment(
                destination=self.accounts[1]['address'],
                asset=Asset.native(),
                amount="40",
            ),
        ))

    def test_mix_1(self):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAADhAAAAAAAAAACAAAAAAAAAAAAAAAJAAAAAAAAAAAAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAAAAAMNQAAAAAAAAAABAAAAAE2ps88xwWiGst/YEzhQ+f8IH+3WNWrTH0MERPmSL9doAAAAAAAAAAAAAw1AAAAAAAAAAAIAAAAAAAAAAAADDUAAAAAAoEATyhnfBjtgSGL5Fr4oHlw/X4bIYnH44zIpor2MQbUAAAAAAAAAAAADDUAAAAAAAAAAAAAAAAMAAAABYmVlcgAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAAAAFiZWVyAAAAAE2ps88xwWiGst/YEzhQ+f8IH+3WNWrTH0MERPmSL9doAAAAAAAPQkAABMsvAAGGoAAAAAAAAAABAAAAAAAAAAQAAAABYmVlcgAAAABNqbPPMcFohrLf2BM4UPn/CB/t1jVq0x9DBET5ki/XaAAAAAFiZWVyAAAAAKBAE8oZ3wY7YEhi+Ra+KB5cP1+GyGJx+OMyKaK9jEG1AAAAAAAPQkAABMsvAAGGoAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAABYmVlcgAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAgxJul41P3AAAAAAAAAAcAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAABYmVlcgAAAAEAAAAAAAAACAAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAAAAAAAAABzT4TYwAAAEC3uXbFZmH4Lfc97n8GXClV5My7ksXlgTxu/DamkMQJkqN95nt3kh8nYAZ0EyINubT7Hldk48CjRmC0Zm6GNxQI'
        assert (result == self.make_envelope(
            CreateAccount(
                destination=self.accounts[0]['address'],
                starting_balance=self.amount,
            ),
            Payment(
                destination=self.accounts[1]['address'],
                asset=Asset.native(),
                amount=self.amount,
            ),
            PathPayment(
                destination=self.accounts[2]['address'],
                send_asset=Asset.native(),
                dest_asset=Asset.native(),
                send_max=self.amount,
                dest_amount=self.amount,
                path=[],
            ),
            ManageOffer(
                selling=Asset('beer', self.accounts[0]['address']),
                buying=Asset('beer', self.accounts[1]['address']),
                amount="100",
                price=3.14159,
                offer_id=1,
            ),
            CreatePassiveOffer(
                selling=Asset('beer', self.accounts[1]['address']),
                buying=Asset('beer', self.accounts[2]['address']),
                amount="100",
                price=3.14159,
            ), SetOptions(),
            ChangeTrust(asset=Asset('beer', self.accounts[0]['address']), ),
            AllowTrust(
                trustor=self.accounts[0]['address'],
                asset_code='beer',
                authorize=True,
            ), AccountMerge(destination=self.accounts[0]['address'], )))

    def test_mix_2(self):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAABkAAAAAAAAAACAAAAAAAAAAAAAAAEAAAAAAAAAAUAAAAAAAAAAAAAAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAABRVVSAAAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAACRhOcqAAAAAAAAAAAAcAAAAA01KM3XCt1+LHD7jDTOYpe/HGKSDoQoyL1JbUOc0+E2MAAAABRVVSAAAAAAEAAAAAAAAAAQAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAAAAFFVVIAAAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAJGE5yoAAAAAAAAAAAAc0+E2MAAABAr3a1mU5aic4bgqsapS8M6EmyPJHNo5/Mk9h2edcExihJ0eoPHjzYXazEVAWg+d5GM182kzwiWvjlbLjPTQQJCA=='
        assert (result == self.make_envelope(
            SetOptions(set_flags=1),
            ChangeTrust(asset=Asset('EUR', self.address), limit="1000000000"),
            AllowTrust(authorize=True, asset_code='EUR', trustor=self.address),
            Payment(
                destination=self.accounts[0]['address'],
                asset=Asset('EUR', self.address),
                amount="1000000000")))

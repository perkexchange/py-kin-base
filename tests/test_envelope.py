# coding:utf-8
from os import path
import pytest

from kin_base.operation import *
from kin_base.asset import Asset
from kin_base.keypair import Keypair
from kin_base.transaction import Transaction
from kin_base.transaction_envelope import TransactionEnvelope as Te


class TestOp:
    source = 'GDJVFDG5OCW5PYWHB64MGTHGFF57DRRJEDUEFDEL2SLNIOONHYJWHA3Z'
    seed = 'SAHPFH5CXKRMFDXEIHO6QATHJCX6PREBLCSFKYXTTCDDV6FJ3FXX4POT'
    dest = 'GCW24FUIFPC2767SOU4JI3JEAXIHYJFIJLH7GBZ2AVCBVP32SJAI53F5'
    amount = "1"

    def do(self, network, op):
        tx = Transaction(self.source, sequence=1)
        tx.add_operation(op)
        envelope = Te(tx, network_id=network)
        signer = Keypair.from_seed(self.seed)
        envelope.sign(signer)
        envelope_b64 = envelope.xdr()
        print(envelope_b64)
        return envelope_b64

    def test_createAccount_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAAAAAAnEAAAAAAAAAABzT4TYwAAAEDtPANNTqbKHS+DnBPj3xCPpp9YPIOmWje9i9EaUZOdCXvC7N0gR5pKyJ9KojGgpkrnHKscxoVH13yrINLzaxgO'
        generated_result = self.do(
            setup.network,
            op=CreateAccount(
                destination=self.dest,
                starting_balance=self.amount,
            ))
        assert result == generated_result

    def test_payment_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAQAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAEAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAAAAAAAAAAAJxAAAAAAAAAAAc0+E2MAAABAu78hB9ELJKA+vQfpnTbNPmVjlg3s3LDwgMmIS/xcvp1Gc64pPLiO1mvUWreo7fJHy0JAjBWlkT51y987f+IrDA=='
        generated_result = self.do(
            setup.network,
            op=Payment(
                source=self.source,
                destination=self.dest,
                asset=Asset.native(),
                amount=self.amount,
            ))
        assert result == generated_result

    def test_payment_short_asset(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAQAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAEAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAABVVNENAAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAAAACcQAAAAAAAAAAHNPhNjAAAAQDcXlsaL4bVvglXAMHCDRTP7/VKNXuZ2pDZG3d972eTFVx2GkmhruBSivk4T8AD4D2p7L2sJb2azmhntPiGYNQ4='
        generated_result = self.do(
            setup.network,
            op=Payment(
                source=self.source,
                destination=self.dest,
                asset=Asset('USD4', self.source),
                amount=self.amount,
            ))
        assert result == generated_result

    def test_payment_long_asset(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAQAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAEAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAACU05BQ0tTNzg5QUJDAAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAAAAAJxAAAAAAAAAAAc0+E2MAAABAXI0LGjLyEHJNsqxjAbN/Ry9eJUo8SWS7iib7QcM0nZOwAzzRICPxyr/ldL777P/p8xsWHA4vvYeNI3tGvkquCQ=='
        generated_result = self.do(
            setup.network,
            op=Payment(
                source=self.source,
                destination=self.dest,
                asset=Asset('SNACKS789ABC', self.source),
                amount=self.amount,
            ))
        assert result == generated_result

    def test_pathPayment_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAQAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAIAAAAAAAAAAAAAJxAAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAAAAAAAAAAAJxAAAAAAAAAAAAAAAAHNPhNjAAAAQEfgQzYr9yUkomEyip17e5al9JAV8puIGS7Rd8An2wdvLjnTBaelTg65mCc4HxetFW98oaMtxhk9M4kUSBrLxgM='
        generated_result = self.do(
            setup.network,
            op=PathPayment(
                source=self.source,
                destination=self.dest,
                send_asset=Asset.native(),
                dest_asset=Asset.native(),
                send_max=self.amount,
                dest_amount=self.amount,
                path=[],
            ))
        assert result == generated_result

    def test_manageOffer_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAMAAAABYmVlcgAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAFiZWVyAAAAAK2uFogrxa/78nU4lG0kBdB8JKhKz/MHOgVEGr96kkCOAAAAAAAPQkAABMsvAAGGoAAAAAAAAAABAAAAAAAAAAHNPhNjAAAAQNM2RVXjN3xGRDuG1KQL0gbf1yidg33HDqRv6IVHeMlo2IurlfBUoeK2tosWIasNWpHnKHGgYo23sBEHl/nXyg0='
        generated_result = self.do(
            setup.network,
            op=ManageOffer(
                selling=Asset('beer', self.source),
                buying=Asset('beer', self.dest),
                amount="100",
                price=3.14159,
                offer_id=1,
            ))
        assert result == generated_result

    def test_createPassiveOffer_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAQAAAABYmVlcgAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAAAAFiZWVyAAAAAK2uFogrxa/78nU4lG0kBdB8JKhKz/MHOgVEGr96kkCOAAAAAAAPQkAABMsvAAGGoAAAAAAAAAABzT4TYwAAAEDI+TDE/LRjNTv0GE/habsS4UgJa+rgzvRsrtfHCTxKer0pMJPMmb9D+Up+o64P1uD9cO5oNtlxK2/BAV9O7OkH'
        generated_result = self.do(
            setup.network,
            op=CreatePassiveOffer(
                selling=Asset('beer', self.source),
                buying=Asset('beer', self.dest),
                amount="100",
                price=3.14159,
            ))
        assert result == generated_result

    def test_SetOptions_empty(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAc0+E2MAAABAffce5U9sUC0cmi3ecjVayerdg+btd5u7fw1XguZO5mp3EjlZwATvCGdbSQbzH2wJrddAix8cHUgvJD1DdXr8DQ=='
        generated_result = self.do(setup.network, op=SetOptions())
        assert result == generated_result

    def test_changeTrust_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAYAAAABYmVlcgAAAACtrhaIK8Wv+/J1OJRtJAXQfCSoSs/zBzoFRBq/epJAjgAgxJul41P3AAAAAAAAAAHNPhNjAAAAQEBZVM8z1iXurqTBMD1rz9fts1JSbUssvRGtmNxq3fYd+mQLlmMjZeutiLy/eiqMQNGEt1JuDvtriXZgsTk14gk='
        generated_result = self.do(
            setup.network, op=ChangeTrust(asset=Asset('beer', self.dest), ))
        assert result == generated_result

    def test_allowTrust_shortAsset(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAcAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAABYmVlcgAAAAEAAAAAAAAAAc0+E2MAAABAV3Lq9RaWrhckFLidPp3WwDnGmJfY/oTQECxJqinkP0PVgS94egZt6bY9hXNWXNrLePID1XpBzVm8K6plpW6qBw=='
        generated_result = self.do(
            setup.network,
            op=AllowTrust(
                trustor=self.dest,
                asset_code='beer',
                authorize=True,
            ))
        assert result == generated_result

    def test_allowTrust_longAsset(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAcAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAACcG9ja2V0a25pdmVzAAAAAQAAAAAAAAABzT4TYwAAAEDGsNazdiNzGOy11OwmnTjRAqZFw3IWasKUrqj7jldElyRYZYILZ56N3PFkIUQXfE4+GI6uiQ3kN8eXQFLXBVUH'
        generated_result = self.do(
            setup.network,
            op=AllowTrust(
                trustor=self.dest,
                asset_code='pocketknives',
                authorize=True,
            ))
        assert result == generated_result

    def test_accountMerge_min(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAgAAAAAra4WiCvFr/vydTiUbSQF0HwkqErP8wc6BUQav3qSQI4AAAAAAAAAAc0+E2MAAABA0CkEVv6elPyZRDX554X2r51z3L1RFxOpdNNT4VHk8C/zi7pUPv92tJB7jZAExkCFOX0nDPYrb74RXYTzVxSZDg=='
        generated_result = self.do(
            setup.network, op=AccountMerge(destination=self.dest))
        assert result == generated_result

    def test_inflation(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAkAAAAAAAAAAc0+E2MAAABAg4Tj3VkLb4/I/BjtdUEoSJRO3plqsw8fApTVazJaYlCafePH3mWcJyQefELPTRlFqbPxyTaQoRD9WK86g0CPAw=='
        generated_result = self.do(setup.network, op=Inflation())
        assert result == generated_result

    def test_manage_data(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAoAAAAiMUtGSEU3dzhCaGFFTkFzd3dyeWFvY2NEYjZxY1Q2RGJZWQAAAAAAAQAAADhHREpWRkRHNU9DVzVQWVdIQjY0TUdUSEdGRjU3RFJSSkVEVUVGREVMMlNMTklPT05IWUpXSEEzWgAAAAAAAAABzT4TYwAAAEAwMGuJaQ2p5FGcFWms7omrCGbph64RslNqNLj5o6SfKFfKviCVbjzVm6FhNA3iOfBcAEPZgnSCcvRsirkiUvwK'
        generated_result = self.do(
            setup.network,
            op=ManageData(
                data_name='1KFHE7w8BhaENAswwryaoccDb6qcT6DbYY',
                data_value=self.source,
            ))
        assert result == generated_result

    def test_bump_sequence(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAZAAAAAAAAAACAAAAAAAAAAAAAAABAAAAAAAAAAsAAAAFbsMSkgAAAAAAAAABzT4TYwAAAEBCy2YhkcyBpz3Wz3BSchLX/0R1GY5aS1LJ3VJigadB8nt6t++/4j/9YEMWWEDl3JhRTOMhPN8SSSs/zK1S1NIM'
        generated_result = self.do(
            setup.network,
            op=BumpSequence(bump_to=23333114514))
        assert result == generated_result


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

    def make_envelope(self, network, *args, **kwargs):
        opts = {'sequence': 1, 'fee': 100 * len(args)}
        for opt, value in kwargs.items():
            opts[opt] = value
        tx = Transaction(self.address, **opts)
        for count, op in enumerate(args):
            tx.add_operation(op)
        envelope = Te(tx, network_id=network)
        signer = Keypair.from_seed(self.seed)
        envelope.sign(signer)
        envelope_b64 = envelope.xdr()
        print(envelope_b64)
        return envelope_b64

    def test_double_create_account(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAyAAAAAAAAAACAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAAAAAMNQAAAAAAAAAAAAAAAAE2ps88xwWiGst/YEzhQ+f8IH+3WNWrTH0MERPmSL9doAAAAAAAGGoAAAAAAAAAAAc0+E2MAAABAVl+LFfja8034SDeaE5YdptrcsDmeRfd0eASPPIcjABx32Wj8pfE5cwSZcgPKStUkVfubnlwu3f034NH9IlNTBQ=='
        generated_result = self.make_envelope(
            setup.network,
            CreateAccount(
                destination=self.accounts[0]['address'],
                starting_balance=self.amount,
            ),
            CreateAccount(
                destination=self.accounts[1]['address'],
                starting_balance="40",
            ),
        )
        assert result == generated_result

    def test_double_payment(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAAyAAAAAAAAAACAAAAAAAAAAAAAAACAAAAAAAAAAEAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAAAAAAAAAADDUAAAAAAAAAAAQAAAABNqbPPMcFohrLf2BM4UPn/CB/t1jVq0x9DBET5ki/XaAAAAAAAAAAAAAYagAAAAAAAAAABzT4TYwAAAECwvAyzCkYHCGbECUBLYkNt/MhP9G4HQ8b8vYYKZ29F3BQCNLtLbAwhya4Hpftte7GgPwRLPw5fewU1px7UQcoL'
        generated_result = self.make_envelope(
            setup.network,
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
        )
        assert result == generated_result

    def test_mix_1(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAADhAAAAAAAAAACAAAAAAAAAAAAAAAJAAAAAAAAAAAAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAAAAAMNQAAAAAAAAAABAAAAAE2ps88xwWiGst/YEzhQ+f8IH+3WNWrTH0MERPmSL9doAAAAAAAAAAAAAw1AAAAAAAAAAAIAAAAAAAAAAAADDUAAAAAAoEATyhnfBjtgSGL5Fr4oHlw/X4bIYnH44zIpor2MQbUAAAAAAAAAAAADDUAAAAAAAAAAAAAAAAMAAAABYmVlcgAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAAAAFiZWVyAAAAAE2ps88xwWiGst/YEzhQ+f8IH+3WNWrTH0MERPmSL9doAAAAAAAPQkAABMsvAAGGoAAAAAAAAAABAAAAAAAAAAQAAAABYmVlcgAAAABNqbPPMcFohrLf2BM4UPn/CB/t1jVq0x9DBET5ki/XaAAAAAFiZWVyAAAAAKBAE8oZ3wY7YEhi+Ra+KB5cP1+GyGJx+OMyKaK9jEG1AAAAAAAPQkAABMsvAAGGoAAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAABYmVlcgAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAgxJul41P3AAAAAAAAAAcAAAAAlMoegcSS0iHsTrJ5XNJH1ri4rO05uVmRHX6dbOj22fgAAAABYmVlcgAAAAEAAAAAAAAACAAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAAAAAAAAABzT4TYwAAAEBe61eGGg88kJsWwKEOZru5atzSpsXDZkixOj3Qy/yfh2YNKQ+1IjlSMDcwzBGpbvJmQrvBFtsUcIQVUC+LnXEK'
        generated_result = self.make_envelope(
            setup.network,
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
            ChangeTrust(
                asset=Asset('beer', self.accounts[0]['address']), ),
            AllowTrust(
                trustor=self.accounts[0]['address'],
                asset_code='beer',
                authorize=True,
            ), AccountMerge(destination=self.accounts[0]['address'], ))
        assert result == generated_result

    def test_mix_2(self, setup):
        result = b'AAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAABkAAAAAAAAAACAAAAAAAAAAAAAAAEAAAAAAAAAAUAAAAAAAAAAAAAAAEAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYAAAABRVVSAAAAAADTUozdcK3X4scPuMNM5il78cYpIOhCjIvUltQ5zT4TYwAACRhOcqAAAAAAAAAAAAcAAAAA01KM3XCt1+LHD7jDTOYpe/HGKSDoQoyL1JbUOc0+E2MAAAABRVVSAAAAAAEAAAAAAAAAAQAAAACUyh6BxJLSIexOsnlc0kfWuLis7Tm5WZEdfp1s6PbZ+AAAAAFFVVIAAAAAANNSjN1wrdfixw+4w0zmKXvxxikg6EKMi9SW1DnNPhNjAAAJGE5yoAAAAAAAAAAAAc0+E2MAAABA8eoqQZLCnXlmJM0m9N/rhe7l2Fe+Q/Rvz8ooTfEtn75CGlO7B9u1dQkuZzo7YJF1/KkjJ4Fz8Va7AW3FJwe/Bw=='
        generated_result = self.make_envelope(
            setup.network,
            SetOptions(set_flags=1),
            ChangeTrust(
                asset=Asset('EUR', self.address), limit="1000000000"),
            AllowTrust(
                authorize=True, asset_code='EUR',
                trustor=self.address),
            Payment(
                destination=self.accounts[0]['address'],
                asset=Asset('EUR', self.address),
                amount="1000000000"))
        assert result == generated_result

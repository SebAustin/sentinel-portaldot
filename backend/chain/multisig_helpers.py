# Multisig pallet helpers — manual asMulti extrinsics for Portaldot (substrate-interface workaround)

from __future__ import annotations

import hashlib
from typing import Any

from substrateinterface import Keypair, SubstrateInterface
from substrateinterface.base import MultiAccountId


def call_hash_hex(call) -> str:
    hex_data = call.data.to_hex()
    digest = hashlib.blake2b(bytes.fromhex(hex_data[2:]), digest_size=32).hexdigest()
    return f"0x{digest}"


def other_signatories(multisig_account: MultiAccountId, signer: Keypair) -> list[str]:
    signer_pk = f"0x{signer.public_key.hex()}"
    return sorted([s for s in multisig_account.signatories if s.lower() != signer_pk.lower()])


def compose_as_multi(
    substrate: SubstrateInterface,
    call,
    signer: Keypair,
    multisig_account: MultiAccountId,
    maybe_timepoint: dict | None,
) -> Any:
    max_weight = substrate.get_payment_info(call, signer)["weight"]
    return substrate.compose_call(
        call_module="Multisig",
        call_function="as_multi",
        call_params={
            "threshold": multisig_account.threshold,
            "other_signatories": other_signatories(multisig_account, signer),
            "maybe_timepoint": maybe_timepoint,
            "call": call,
            "store_call": False,
            "max_weight": max_weight,
        },
    )


def submit_as_multi(
    substrate: SubstrateInterface,
    call,
    signer: Keypair,
    multisig_account: MultiAccountId,
    maybe_timepoint: dict | None = None,
):
    ms_call = compose_as_multi(substrate, call, signer, multisig_account, maybe_timepoint)
    extrinsic = substrate.create_signed_extrinsic(call=ms_call, keypair=signer)
    return substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)


def get_multisig_timepoint(substrate: SubstrateInterface, multisig_address: str, call_hash: str):
    pending = substrate.query("Multisig", "Multisigs", [multisig_address, call_hash])
    if pending.value is None:
        return None
    return pending.value["when"]

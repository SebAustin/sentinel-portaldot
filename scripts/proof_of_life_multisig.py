# Proof-of-life — 2-of-3 Portaldot multisig transfer via substrate-interface multisig pallet
"""SDK smoke test: Alice proposes, Bob finalizes a POT transfer from multisig account."""

from __future__ import annotations

import os
import sys

from substrateinterface import Keypair, SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from backend.chain.multisig_helpers import (
    call_hash_hex,
    get_multisig_timepoint,
    submit_as_multi,
)

WS_URL = os.getenv("PORTALDOT_WS_URL", "ws://127.0.0.1:9944")
SS58_FORMAT = int(os.getenv("PORTALDOT_SS58_FORMAT", "42"))
TYPE_REGISTRY_PRESET = os.getenv("PORTALDOT_TYPE_REGISTRY_PRESET", "polkadot")
THRESHOLD = 2
TRANSFER_AMOUNT = 10_000_000_000_000_000  # 1 POT (14 decimals on Portaldot)


def connect() -> SubstrateInterface:
    return SubstrateInterface(
        url=WS_URL,
        ss58_format=SS58_FORMAT,
        type_registry_preset=TYPE_REGISTRY_PRESET,
    )


def main() -> int:
    print(f"Connecting to {WS_URL} ...")
    try:
        substrate = connect()
    except Exception as exc:
        print(f"Connection failed: {exc}")
        print("Start Portaldot dev node: ./portaldot_dev --dev --tmp")
        return 1

    keypair_alice = Keypair.create_from_uri("//Alice", ss58_format=substrate.ss58_format)
    keypair_bob = Keypair.create_from_uri("//Bob", ss58_format=substrate.ss58_format)
    keypair_charlie = Keypair.create_from_uri("//Charlie", ss58_format=substrate.ss58_format)

    signatories = sorted(
        [
            keypair_alice.ss58_address,
            keypair_bob.ss58_address,
            keypair_charlie.ss58_address,
        ]
    )

    multisig_account = substrate.generate_multisig_account(
        signatories=signatories,
        threshold=THRESHOLD,
    )
    print(f"Multisig address: {multisig_account.ss58_address}")
    print(f"Signatories ({THRESHOLD}-of-{len(signatories)}): {signatories}")

    fund_call = substrate.compose_call(
        call_module="Balances",
        call_function="transfer_keep_alive",
        call_params={
            "dest": multisig_account.ss58_address,
            "value": 10 * TRANSFER_AMOUNT,
        },
    )
    fund_ext = substrate.create_signed_extrinsic(call=fund_call, keypair=keypair_alice)
    try:
        fund_receipt = substrate.submit_extrinsic(fund_ext, wait_for_inclusion=True)
        if not fund_receipt.is_success:
            print(f"Fund transfer failed: {fund_receipt.error_message}")
            return 1
        print(f"Funded multisig: {fund_receipt.extrinsic_hash}")
    except SubstrateRequestException as exc:
        print(f"Fund transfer error: {exc}")
        return 1

    payment_call = substrate.compose_call(
        call_module="Balances",
        call_function="transfer_keep_alive",
        call_params={
            "dest": keypair_charlie.ss58_address,
            "value": TRANSFER_AMOUNT,
        },
    )
    payment_hash = call_hash_hex(payment_call)
    print(f"Payment call hash: {payment_hash}")

    print("Step 1: Alice initiates multisig proposal ...")
    try:
        propose_receipt = submit_as_multi(
            substrate,
            payment_call,
            keypair_alice,
            multisig_account,
            maybe_timepoint=None,
        )
    except SubstrateRequestException as exc:
        print(f"Propose error: {exc}")
        return 1

    if not propose_receipt.is_success:
        print(f"Propose failed: {propose_receipt.error_message}")
        return 1
    print(f"Proposal extrinsic: {propose_receipt.extrinsic_hash}")

    timepoint = get_multisig_timepoint(substrate, multisig_account.ss58_address, payment_hash)
    print(f"Timepoint: {timepoint}")

    print("Step 2: Bob approves and executes multisig ...")
    try:
        approve_receipt = submit_as_multi(
            substrate,
            payment_call,
            keypair_bob,
            multisig_account,
            maybe_timepoint=timepoint,
        )
    except SubstrateRequestException as exc:
        print(f"Approve error: {exc}")
        return 1

    if not approve_receipt.is_success:
        print(f"Approve failed: {approve_receipt.error_message}")
        return 1

    print(f"Executed extrinsic: {approve_receipt.extrinsic_hash}")
    print(f"Block: {approve_receipt.block_hash}")
    print("Proof-of-life PASSED — Portaldot multisig pallet operational")
    return 0


if __name__ == "__main__":
    sys.exit(main())

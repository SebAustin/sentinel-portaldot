# Portaldot chain service — multisig pallet + balances via substrate-interface

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from substrateinterface import Keypair, SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException

from backend.chain.multisig_helpers import (
    call_hash_hex,
    get_multisig_timepoint,
    submit_as_multi,
)
from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MultisigConfig:
    threshold: int
    signatories: list[str]
    ss58_address: str


@dataclass
class ProposeResult:
    call_hash: str
    propose_tx_hash: str
    block_hash: str
    timepoint: dict[str, int]
    max_weight: dict[str, int]
    multisig_address: str
    threshold: int
    signatories: list[str]
    call_hex: str


class PortaldotChain:
    def __init__(self) -> None:
        self._substrate: SubstrateInterface | None = None
        self._multisig: MultisigConfig | None = None

    @property
    def substrate(self) -> SubstrateInterface:
        if self._substrate is None:
            self._substrate = SubstrateInterface(
                url=settings.portaldot_ws_url,
                ss58_format=settings.portaldot_ss58_format,
                type_registry_preset=settings.portaldot_type_registry_preset,
            )
        return self._substrate

    def health(self) -> dict[str, Any]:
        try:
            block = self.substrate.get_block()
            return {
                "connected": True,
                "endpoint": settings.portaldot_ws_url,
                "block_number": block["header"]["number"],
                "block_hash": block["header"]["hash"],
            }
        except Exception as exc:
            logger.warning("Chain health check failed: %s", exc)
            return {
                "connected": False,
                "endpoint": settings.portaldot_ws_url,
                "error": str(exc),
            }

    def get_demo_keypairs(self) -> tuple[Keypair, Keypair, Keypair]:
        substrate = self.substrate
        alice = Keypair.create_from_uri("//Alice", ss58_format=substrate.ss58_format)
        bob = Keypair.create_from_uri("//Bob", ss58_format=substrate.ss58_format)
        charlie = Keypair.create_from_uri("//Charlie", ss58_format=substrate.ss58_format)
        return alice, bob, charlie

    def get_demo_multisig(self) -> MultisigConfig:
        if self._multisig is not None:
            return self._multisig
        substrate = self.substrate
        alice, bob, charlie = self.get_demo_keypairs()
        signatories = sorted([alice.ss58_address, bob.ss58_address, charlie.ss58_address])
        account = substrate.generate_multisig_account(
            signatories=signatories,
            threshold=settings.multisig_threshold,
        )
        self._multisig = MultisigConfig(
            threshold=settings.multisig_threshold,
            signatories=signatories,
            ss58_address=account.ss58_address,
        )
        return self._multisig

    def pot_to_planck(self, amount_pot: float) -> int:
        return int(amount_pot * (10**settings.pot_decimals))

    def planck_to_pot(self, planck: int) -> float:
        return planck / (10**settings.pot_decimals)

    def query_balance(self, address: str) -> dict[str, Any]:
        result = self.substrate.query("System", "Account", [address])
        free = result.value["data"]["free"]
        return {
            "address": address,
            "free_planck": free,
            "free_pot": self.planck_to_pot(free),
        }

    def ensure_multisig_funded(self, min_pot: float = 10.0) -> None:
        multisig = self.get_demo_multisig()
        balance = self.query_balance(multisig.ss58_address)
        if balance["free_pot"] >= min_pot:
            return
        alice, _, _ = self.get_demo_keypairs()
        amount = self.pot_to_planck(min_pot * 2)
        call = self.substrate.compose_call(
            call_module="Balances",
            call_function="transfer_keep_alive",
            call_params={"dest": multisig.ss58_address, "value": amount},
        )
        extrinsic = self.substrate.create_signed_extrinsic(call=call, keypair=alice)
        receipt = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        if not receipt.is_success:
            raise SubstrateRequestException(f"Fund multisig failed: {receipt.error_message}")

    def compose_transfer_call(self, dest: str, amount_pot: float):
        return self.substrate.compose_call(
            call_module="Balances",
            call_function="transfer_keep_alive",
            call_params={
                "dest": dest,
                "value": self.pot_to_planck(amount_pot),
            },
        )

    def call_hash(self, call) -> str:
        return call_hash_hex(call)

    def propose_multisig_transfer(self, dest: str, amount_pot: float) -> ProposeResult:
        self.ensure_multisig_funded()
        substrate = self.substrate
        multisig_cfg = self.get_demo_multisig()
        multisig_account = substrate.generate_multisig_account(
            signatories=multisig_cfg.signatories,
            threshold=multisig_cfg.threshold,
        )
        proposer = Keypair.create_from_uri(
            settings.proposer_seed,
            ss58_format=substrate.ss58_format,
        )
        call = self.compose_transfer_call(dest, amount_pot)
        receipt = submit_as_multi(
            substrate,
            call,
            proposer,
            multisig_account,
            maybe_timepoint=None,
        )
        if not receipt.is_success:
            raise SubstrateRequestException(f"Multisig propose failed: {receipt.error_message}")

        payment_hash = call_hash_hex(call)
        max_weight = substrate.get_payment_info(call, proposer)["weight"]
        timepoint = get_multisig_timepoint(substrate, multisig_cfg.ss58_address, payment_hash) or {
            "height": receipt.block_number,
            "index": receipt.extrinsic_idx,
        }

        return ProposeResult(
            call_hash=payment_hash,
            propose_tx_hash=receipt.extrinsic_hash,
            block_hash=receipt.block_hash,
            timepoint=timepoint,
            max_weight={"ref_time": max_weight, "proof_size": 0}
            if isinstance(max_weight, int)
            else max_weight,
            multisig_address=multisig_cfg.ss58_address,
            threshold=multisig_cfg.threshold,
            signatories=multisig_cfg.signatories,
            call_hex=call.data.to_hex(),
        )

    def finalize_multisig_transfer(
        self,
        dest: str,
        amount_pot: float,
        approver_seed: str = "//Bob",
        call_hash: str | None = None,
        timepoint: dict | None = None,
    ) -> dict[str, str]:
        substrate = self.substrate
        multisig_cfg = self.get_demo_multisig()
        multisig_account = substrate.generate_multisig_account(
            signatories=multisig_cfg.signatories,
            threshold=multisig_cfg.threshold,
        )
        approver = Keypair.create_from_uri(approver_seed, ss58_format=substrate.ss58_format)
        call = self.compose_transfer_call(dest, amount_pot)
        payment_hash = call_hash or call_hash_hex(call)
        tp = timepoint or get_multisig_timepoint(substrate, multisig_cfg.ss58_address, payment_hash)
        receipt = submit_as_multi(
            substrate,
            call,
            approver,
            multisig_account,
            maybe_timepoint=tp,
        )
        if not receipt.is_success:
            raise SubstrateRequestException(f"Multisig finalize failed: {receipt.error_message}")
        return {
            "execute_tx_hash": receipt.extrinsic_hash,
            "block_hash": receipt.block_hash,
        }

    def get_multisig_pending(self, call_hash: str) -> dict[str, Any] | None:
        multisig = self.get_demo_multisig()
        result = self.substrate.query(
            "Multisig",
            "Multisigs",
            [multisig.ss58_address, call_hash],
        )
        if result.value is None:
            return None
        return result.value


@lru_cache
def get_chain() -> PortaldotChain:
    return PortaldotChain()

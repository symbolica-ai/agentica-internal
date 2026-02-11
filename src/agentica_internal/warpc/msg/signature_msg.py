# fmt: off

from .__ import *
from .term import TermPassByValMsg
from .msg_aliases import AnnotationsMsg, AttributesMsg

__all__ = [
    'SignatureMsg',
    'enc_signature',
    'dec_signature',
]

################################################################################

class SignatureMsg(TermPassByValMsg, tag='sig'):

    type V = Signature

    pos_args:  strtup = ()
    key_args:  strtup = ()
    pos_star:  optstr = None
    key_star:  optstr = None
    pos_only:  int = 0
    is_coro:   bool = False
    optional:  strtup = ()
    defaults: 'AttributesMsg' = {}
    annos:    'AnnotationsMsg' = {}
    doc:       optstr = None
    next_over: 'SignatureMsg | None' = None

    def __shape__(self):
        co = '!' if self.is_coro else ''
        po = 'p' * self.pos_only
        pa = 'a' * (len(self.pos_args) - self.pos_only)
        ps = ',*,' if self.pos_star else ''
        ka = 'k' * len(self.pos_args)
        ks = ',**,' if self.key_star else ''
        df = '=' * len(self.defaults)
        an = ':' * len(self.annos)
        ex = ';...' if self.next_over else ''
        return f'{co}{po}{pa}{ps}{ka}{ks}{df}{an}{ex}'

    def __debug_info_str__(self) -> str:
        return "\"" + self.__shape__() + "\""

    @classmethod
    def encode_compound(cls, term: Signature, enc: EncoderP) -> 'SignatureMsg':
        return enc_signature(term, enc)

    def decode(self, dec: DecoderP) -> Signature:
        return dec_signature(self, dec)

################################################################################

def enc_signature(term: Signature, enc: EncoderP) -> SignatureMsg:
    enc_term = enc.enc_any
    defs = tuple(term.defaults.items())
    next_over = term.next_over
    return SignatureMsg(
        pos_args=term.pos_args,
        key_args=term.key_args,
        pos_star=term.pos_star,
        key_star=term.key_star,
        pos_only=term.pos_only,
        is_coro=term.is_coro,
        optional=tuple(k for k, v in defs if v is ARG_DEFAULT),
        defaults={k: enc_term(v) for k, v in defs if v is not ARG_DEFAULT},
        annos=enc.enc_annotations(term.annos),
        doc=term.doc_str,
        next_over=enc_signature(next_over, enc) if next_over is not None else None
    )

def dec_signature(msg: SignatureMsg, dec: DecoderP) -> Signature:
    next_over = msg.next_over
    return Signature(
        pos_args=msg.pos_args,
        key_args=msg.key_args,
        pos_star=msg.pos_star,
        key_star=msg.key_star,
        pos_only=msg.pos_only,
        optional=msg.optional,
        is_coro=msg.is_coro,
        defaults=dec.dec_record(msg.defaults),
        annos=dec.dec_annotations(msg.annos),
        doc_str=msg.doc,
        next_over=dec_signature(next_over, dec) if next_over is not None else None
    )

def dec_signature_partial(msg: SignatureMsg) -> Signature:
    return Signature(
        pos_args=msg.pos_args,
        key_args=msg.key_args,
        pos_star=msg.pos_star,
        key_star=msg.key_star,
        pos_only=msg.pos_only,
        optional=msg.optional,
        is_coro=msg.is_coro,
        defaults=dict.fromkeys(msg.defaults),
        annos=dict.fromkeys(msg.annos, ...),
        next_over=dec_signature_partial(msg.next_over) if msg.next_over is not None else None
    )

# coding: utf-8

from cprocsp import csp, rdn
from nose.tools import raises
from uuid import uuid4
import subprocess as sub
import os
from base64 import b64encode

enc_type = csp.X509_ASN_ENCODING | csp.PKCS_7_ASN_ENCODING
flags = 0


def _context_simple():
    context = csp.Crypt(
        None,
        csp.PROV_GOST_2001_DH,
        csp.CRYPT_VERIFYCONTEXT,
    )
    assert context
    return context


def _context_named():
    ur''' Работает при наличии в системе контейнера 'test'.
    Необходимо его предварительно создать командой:

    csptestf -keyset -newkeyset -cont '\\.\hdimage\test'

    '''
    context = csp.Crypt(
        "test",
        csp.PROV_GOST_2001_DH,
        0,
    )
    assert context
    return context


@raises(SystemError)
def test_context_bad():
    csp.Crypt(
        "some_wrong_ctx",
        csp.PROV_GOST_2001_DH,
        0,
    )


def test_store():
    cs = csp.CertStore(None, "MY")
    assert cs


def test_store_in_context():
    context = _context_simple()
    cs = csp.CertStore(context, "MY")
    assert cs


def test_store_iter():
    ur''' Работает при наличии в системе как минимум одного сертификата.

    Тестовый сертификат создается следующим образом:

    Запрос на сертификат

        cryptcp -creatrqst -cont '\\.\hdimage\test' -provtype 75 -nokeygen -dn 'E=test@localhost.localdomain,CN=test' -both ~/req

    Затем следует получить сертификат вручную от тестового УЦ по адресу: http://www.cryptopro.ru/certsrv

    И установить сохраненный сертификат в хранилище:

        cryptcp -instcert -cont '\\.\hdimage\test' ИмяФайла.cert'''

    cs = csp.CertStore(None, "MY")
    assert len(list(cs))


def _cert_thumb():
    cs = csp.CertStore(None, "MY")
    thumbs = [cert.thumbprint() for cert in cs]
    assert thumbs
    return thumbs[0]


def test_cert_name():
    cs = csp.CertStore(None, "MY")
    names = list(cert.name() for cert in cs)
    print names
    assert all(name for name in names)


def test_cert_issuer():
    cs = csp.CertStore(None, "MY")
    issuers = list(cert.issuer() for cert in cs)
    print issuers
    assert all(s for s in issuers)


def test_cert_find_by_thumb():
    thumb = _cert_thumb()
    cs = csp.CertStore(None, "MY")
    res = list(cs.find_by_thumb(thumb))
    assert len(res)


def test_cert_find_by_name():
    name = 'test'
    cs = csp.CertStore(None, "MY")
    res = list(cs.find_by_name(name))
    assert len(res)


def test_memory_store():
    my = csp.CertStore(None, "MY")
    cert = list(my)[0]

    cs = csp.CertStore()
    cs.add_cert(cert)

    assert len(list(cs))


def test_cert_not_found():
    cs = csp.CertStore(None, "MY")
    res = list(cs.find_by_thumb('x' * 20))
    assert not len(res)


def test_cert_name_not_found():
    cs = csp.CertStore(None, "MY")
    res = list(cs.find_by_name('some wrong name'))
    assert not len(res)


def test_cert_sign_algorithm():
    cs = csp.CertStore(None, "MY")
    cert = list(cs)[0]
    assert cert.sign_algorithm() == '1.2.643.2.2.3'


def _msg_decode():
    testdata = open('tests/logical.cms', 'rb').read()
    msg = csp.CryptMsg(testdata)
    return msg


def test_sign_data():
    ctx = csp.Crypt(
        "test",
        csp.PROV_GOST_2001_DH,
        0,
    )
    cs = csp.CertStore(ctx, "MY")
    cert = list(cs)[0]
    mess = csp.CryptMsg(ctx)
    mess.add_signer_cert(cert)
    data = mess.sign_data('hurblewurble')
    assert len(data)
    return data


def test_detached_sign():
    ctx = csp.Crypt(
        "test",
        csp.PROV_GOST_2001_DH,
        0,
    )
    cs = csp.CertStore(ctx, "MY")
    cert = list(cs)[0]
    mess = csp.CryptMsg(ctx)
    mess.add_signer_cert(cert)
    data = mess.sign_data('hurblewurble', True)
    assert len(data)
    return data


def test_cert_from_detached():
    sgn = test_detached_sign()
    mess = csp.CryptMsg(sgn)
    assert len(list(mess.certs))


def test_verify_with_detached():
    sgn = test_detached_sign()
    msg = csp.CryptMsg(sgn)
    for n in range(msg.num_signers):
        assert msg.verify_data('hurblewurble', n)


def test_verify_with_detached_bad():
    sgn = test_detached_sign()
    msg = csp.CryptMsg(sgn)
    for n in range(msg.num_signers):
        assert not msg.verify_data('hUrbLewUrblE', n)


def setup_module():
    global signname
    signname = os.path.join('/tmp', uuid4().hex)
    open(signname, 'wb').write('hurblewurble')
    if sub.call(['/opt/cprocsp/bin/ia32/cryptcp', '-dir', '/tmp', '-signf', '-nochain', '-cert', '-der', signname]):
        assert False


def test_msg_signatures():
    ctx = csp.Crypt(
        None,
        csp.PROV_GOST_2001_DH,
        csp.CRYPT_VERIFYCONTEXT,
    )
    testdata = test_sign_data()
    # testdata = open('tests/logical.cms', 'rb').read()
    msg = csp.CryptMsg(testdata, ctx)
    del testdata
    print msg.type
    print msg.num_signers
    print len(msg.get_data())

    psi = msg.get_nth_signer_info(0)
    assert psi
    my = msg.certs
    verify_cert = my.get_cert_by_info(psi)

    print verify_cert.name()
    assert msg.verify_cert(verify_cert)
    ns = list(c.name() for c in msg.signer_certs())
    assert len(ns)
    cs = list(msg.certs)
    print [(msg.verify_cert(x), x.name()) for x in cs]
    assert all(msg.verify_cert(c) for c in cs)


def test_verify_file():
    names = ('data1', 'data2')
    for name in names:
        data = open('tests/{0}.bin'.format(name), 'rb').read()
        sig = open('tests/{0}.p7s'.format(name), 'rb').read()
        vrf = csp.CryptMsg(sig)
        print vrf.num_signers
        for c in vrf.certs:
            print unicode(c.name(), 'windows-1251')
            print unicode(c.issuer(), 'windows-1251')
            print b64encode(c.thumbprint())
        assert all(vrf.verify_data(data, x) for x in range(vrf.num_signers))


def test_rdn():
    dn = u'''1.2.643.3.141.1.2 = \\#0C0430303030 , 1.2.643.3.141.1.1="#0C0A30303030303030303030",
    1.2.643.3.131.1.1="#0C0A36363939303030303030", E=fedotov@skbkontur.ru,
    C=RU, S=66 Свердловская область + L=Екатеринбург, O=ЗАО ПФ СКБ Контур, OU=0,
    CN=Федотов Алексей Николаевич,
    1.2.840.113549.1.9.2="#0C21363639393030303030302D3636393930313030312D363630393033303338363334",
    T=Инженер-программист, SN=Федотов Алексей Николаевич
    '''
    print dict(rdn.read_rdn(dn))


def test_cert_rdn():
    cs = csp.CertStore(None, "MY")
    for c in cs:
        assert 'CN' in c.info
        assert 'CN' in c.issuer_info

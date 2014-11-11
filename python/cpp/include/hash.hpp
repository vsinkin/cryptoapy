#ifndef HASH_HPP_INCLUDED
#define HASH_HPP_INCLUDED

#include "common.hpp"
#include "rcobj.hpp"
#include "except.hpp"

class Crypt;


/**
 * Provides simple hash functions, like data hash calculation, signing and
 * veriying hashes. Used primarily for XML DSIG, for general message signing
 * and verifying see `Msg` class.
 */
class Hash : public RCObj
{
private:
    HCRYPTHASH hhash;
    Crypt *parent;
    void init(Crypt *ctx) throw(CSPException);
protected:
    //
public:
    Hash(Crypt *ctx, BYTE *STRING, DWORD LENGTH) throw(CSPException);
    Hash(Crypt *ctx) throw(CSPException);

    virtual ~Hash() throw(CSPException);

    void digest(BYTE **s, DWORD *slen) throw(CSPException);
    void update(BYTE *STRING, DWORD LENGTH) throw(CSPException);
    void sign(DWORD dwKeyspec, BYTE **s, DWORD *slen) throw(CSPException);

    friend class Crypt;
};

#endif

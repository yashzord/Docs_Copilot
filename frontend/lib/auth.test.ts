// Tests for the PKCE challenge. Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";

import { sha256Base64Url } from "./auth.ts";

test("hashes the verifier the way Cognito's PKCE example does", async () => {
  // The verifier and challenge pair from the Cognito developer guide, PKCE page.
  const verifier =
    "9D-aW_iygXrgQcWJd0y0tNVMPSXSChIc2xceDhvYVdGLCBk-JWFTmBNjvKSdOrjTTYazOFbUmrFERrjWx6oKtK2b6z_x4_gHBDlr4K1mRFGyE8yA-05-_v7Dxf3EIYJH";

  assert.equal(await sha256Base64Url(verifier), "Eh0mg-OZv7BAyo-tdv_vYamx1boOYDulDklyXoMDtLg");
});

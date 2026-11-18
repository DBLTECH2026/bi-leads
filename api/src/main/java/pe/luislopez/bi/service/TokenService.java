package pe.luislopez.bi.service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/** Clave simple de acceso: quien la sabe recibe un token firmado (HMAC-SHA256) válido por 12 horas. */
@Service
public class TokenService {
    public static final long DURACION_SEG = 12 * 3600;
    private static final Base64.Encoder B64 = Base64.getUrlEncoder().withoutPadding();

    private final byte[] clave;
    private final byte[] secreto;

    public TokenService(@Value("${bi.clave}") String clave, @Value("${bi.secreto}") String secreto) {
        this.clave = clave.getBytes(StandardCharsets.UTF_8);
        this.secreto = secreto.getBytes(StandardCharsets.UTF_8);
    }

    public boolean claveCorrecta(String intento) {
        return intento != null && MessageDigest.isEqual(clave, intento.getBytes(StandardCharsets.UTF_8));
    }

    public String emitir() {
        String expira = String.valueOf(Instant.now().getEpochSecond() + DURACION_SEG);
        return B64.encodeToString(expira.getBytes(StandardCharsets.UTF_8)) + "." + firma(expira);
    }

    public boolean valido(String token) {
        if (token == null || !token.contains(".")) {
            return false;
        }
        String[] partes = token.split("\\.", 2);
        try {
            String expira = new String(Base64.getUrlDecoder().decode(partes[0]), StandardCharsets.UTF_8);
            boolean firmaOk = MessageDigest.isEqual(firma(expira).getBytes(StandardCharsets.UTF_8),
                    partes[1].getBytes(StandardCharsets.UTF_8));
            return firmaOk && Long.parseLong(expira) > Instant.now().getEpochSecond();
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    private String firma(String texto) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secreto, "HmacSHA256"));
            return B64.encodeToString(mac.doFinal(texto.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new IllegalStateException("No se pudo firmar el token", e);
        }
    }
}

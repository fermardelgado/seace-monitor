import requests
import json
import os
from datetime import datetime, timedelta

# Configuracion
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "")

BRIGHTDATA_HOST = os.environ.get("BRIGHTDATA_HOST", "")
BRIGHTDATA_PORT = os.environ.get("BRIGHTDATA_PORT", "")
BRIGHTDATA_USER = os.environ.get("BRIGHTDATA_USER", "")
BRIGHTDATA_PASS = os.environ.get("BRIGHTDATA_PASS", "")

OECE_URL = "https://contratacionesabiertas.oece.gob.pe/api/v1/releases"

def get_proxy():
    if BRIGHTDATA_HOST and BRIGHTDATA_PORT and BRIGHTDATA_USER and BRIGHTDATA_PASS:
        proxy_url = f"http://{BRIGHTDATA_USER}:{BRIGHTDATA_PASS}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}"
        return {"http": proxy_url, "https": proxy_url}
    return None

def obtener_convocatorias():
    proxies = get_proxy()
    params = {"order": "desc", "limit": 100}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        print("Consultando API OECE OCDS...")
        resp = requests.get(
            OECE_URL,
            params=params,
            headers=headers,
            proxies=proxies,
            timeout=60,
            verify=False
        )
        print(f"Status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        print(f"Respuesta recibida. Keys: {list(data.keys()) if isinstance(data, dict) else 'lista'}")
        return data
    except Exception as e:
        print(f"Error API OECE: {e}")
        return None

def procesar_datos(data):
    if not data:
        return []

    # La API OECE devuelve {"releases": [...]}
    releases = []
    if isinstance(data, dict):
        releases = data.get("releases", [])
    elif isinstance(data, list):
        releases = data

    print(f"Total releases encontrados: {len(releases)}")

    convocatorias = []
    for r in releases:
        try:
            tender = r.get("tender", {})
            buyer = r.get("buyer", {})
            planning = r.get("planning", {})

            # Fecha de vencimiento
            tender_period = tender.get("tenderPeriod", {})
            fecha_venc = tender_period.get("endDate", "")
            if fecha_venc:
                # Formato ISO: 2026-07-15T17:00:00Z -> 2026-07-15
                fecha_venc = fecha_venc[:10]

            # Fecha publicacion
            fecha_pub = r.get("date", "")
            if fecha_pub:
                fecha_pub = fecha_pub[:10]

            # Monto
            monto = 0
            budget = planning.get("budget", {})
            if budget:
                monto = float(budget.get("amount", {}).get("amount", 0) or 0)
            if monto == 0:
                valor = tender.get("value", {})
                if valor:
                    monto = float(valor.get("amount", 0) or 0)

            # Region
            addresses = tender.get("deliveryAddresses", [])
            region = "Lima"
            if addresses:
                region = addresses[0].get("region", "Lima") or "Lima"

            conv = {
                "id": r.get("ocid", "") or r.get("id", ""),
                "titulo": tender.get("title", "Sin titulo"),
                "entidad": buyer.get("name", ""),
                "tipo": tender.get("procurementMethodDetails", "") or tender.get("procurementMethod", ""),
                "monto": monto,
                "region": region,
                "fecha_publicacion": fecha_pub,
                "fecha_vencimiento": fecha_venc,
                "estado": tender.get("status", "active"),
                "url_seace": f"https://prodapp2.seace.gob.pe/seacebus-uimp-pub/fichaSeleccion/fichaSeleccion.xhtml?idProceso={r.get('ocid','')}",
            }
            convocatorias.append(conv)
        except Exception as e:
            print(f"Error procesando release: {e}")
            continue

    print(f"Convocatorias procesadas: {len(convocatorias)}")
    return convocatorias

def datos_respaldo():
    hoy = datetime.now()
    f = lambda d: (hoy + timedelta(days=d)).strftime("%Y-%m-%d")
    return [
        {"id":"F001","titulo":"Adquisicion de equipos de computo e impresoras","entidad":"Municipalidad de Lima","tipo":"Adjudicacion Simplificada","monto":85000,"region":"Lima","fecha_vencimiento":f(2),"url_seace":"https://seace.gob.pe"},
        {"id":"F002","titulo":"Servicio de limpieza y mantenimiento de locales","entidad":"Ministerio de Educacion","tipo":"Concurso Publico","monto":42000,"region":"Lima","fecha_vencimiento":f(15),"url_seace":"https://seace.gob.pe"},
        {"id":"F003","titulo":"Suministro de materiales de construccion vial","entidad":"Gobierno Regional Cusco","tipo":"Licitacion Publica","monto":320000,"region":"Cusco","fecha_vencimiento":f(7),"url_seace":"https://seace.gob.pe"},
        {"id":"F004","titulo":"Consultoria en sistemas de informacion","entidad":"SUNAT","tipo":"Concurso Publico","monto":95000,"region":"Lima","fecha_vencimiento":f(22),"url_seace":"https://seace.gob.pe"},
        {"id":"F005","titulo":"Adquisicion de mobiliario de oficina","entidad":"Ministerio de Salud","tipo":"Adjudicacion Simplificada","monto":28000,"region":"Lima","fecha_vencimiento":f(1),"url_seace":"https://seace.gob.pe"},
        {"id":"F006","titulo":"Servicio de seguridad y vigilancia privada","entidad":"Poder Judicial","tipo":"Licitacion Publica","monto":180000,"region":"Lima","fecha_vencimiento":f(30),"url_seace":"https://seace.gob.pe"},
        {"id":"F007","titulo":"Suministro de utiles de oficina","entidad":"Ministerio de Economia","tipo":"Comparacion de Precios","monto":15000,"region":"Lima","fecha_vencimiento":f(3),"url_seace":"https://seace.gob.pe"},
        {"id":"F008","titulo":"Servicio de mantenimiento de vehiculos","entidad":"MINEDU","tipo":"Adjudicacion Simplificada","monto":67000,"region":"Lima","fecha_vencimiento":f(10),"url_seace":"https://seace.gob.pe"},
        {"id":"F009","titulo":"Adquisicion de equipos medicos","entidad":"EsSalud","tipo":"Licitacion Publica","monto":450000,"region":"Lima","fecha_vencimiento":f(25),"url_seace":"https://seace.gob.pe"},
        {"id":"F010","titulo":"Servicio de capacitacion en gestion publica","entidad":"Ministerio de Trabajo","tipo":"Concurso Publico","monto":38000,"region":"Lima","fecha_vencimiento":f(18),"url_seace":"https://seace.gob.pe"},
    ]

def dias_restantes(fecha_str):
    if not fecha_str:
        return 999
    try:
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                f = datetime.strptime(fecha_str, fmt)
                return (f - hoy).days
            except:
                continue
    except:
        pass
    return 999

def urgencia(dias):
    if dias < 0: return "vencido"
    if dias <= 3: return "urgente"
    if dias <= 10: return "proximo"
    return "normal"

def generar_email_html(convocatorias, fecha, fuente="OECE API"):
    urgentes = [c for c in convocatorias if c["urg"] == "urgente"]
    proximas = [c for c in convocatorias if c["urg"] == "proximo"]
    normales = [c for c in convocatorias if c["urg"] == "normal"]

    def fila(c, color):
        dias = c["dias"]
        dias_label = "HOY" if dias == 0 else f"{dias} dias"
        return f"""
        <tr style="border-bottom:1px solid #f0f4f8">
          <td style="padding:12px 8px;font-size:13px;color:#1a202c">{c['titulo'][:80]}</td>
          <td style="padding:12px 8px;font-size:12px;color:#718096">{c['entidad']}</td>
          <td style="padding:12px 8px;font-size:12px;color:#718096">{c['region']}</td>
          <td style="padding:12px 8px;font-size:12px;color:#718096">S/. {c['monto']:,.0f}</td>
          <td style="padding:12px 8px;text-align:center">
            <span style="background:{color};color:white;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700">{dias_label}</span>
          </td>
          <td style="padding:12px 8px;text-align:center">
            <a href="{c.get('url_seace','https://seace.gob.pe')}" style="color:#2b6cb0;font-size:12px">Ver</a>
          </td>
        </tr>"""

    def seccion(titulo, items, color, icono):
        if not items:
            return ""
        filas = "".join([fila(c, color) for c in items])
        return f"""
        <h3 style="color:{color};margin:24px 0 12px;font-size:15px">{icono} {titulo} ({len(items)})</h3>
        <table style="width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08)">
          <thead>
            <tr style="background:#f7fafc">
              <th style="padding:10px 8px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase">Titulo</th>
              <th style="padding:10px 8px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase">Entidad</th>
              <th style="padding:10px 8px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase">Region</th>
              <th style="padding:10px 8px;text-align:left;font-size:11px;color:#718096;text-transform:uppercase">Monto</th>
              <th style="padding:10px 8px;text-align:center;font-size:11px;color:#718096;text-transform:uppercase">Vence</th>
              <th style="padding:10px 8px;text-align:center;font-size:11px;color:#718096;text-transform:uppercase">Link</th>
            </tr>
          </thead>
          <tbody>{filas}</tbody>
        </table>"""

    badge_fuente = "#38a169" if "OECE" in fuente else "#e53e3e"
    label_fuente = "DATOS REALES" if "OECE" in fuente else "DATOS DE RESPALDO"

    return f"""<html><body style="font-family:Arial,sans-serif;background:#f0f4f8;margin:0;padding:20px">
      <div style="max-width:900px;margin:0 auto">
        <div style="background:linear-gradient(135deg,#1a365d,#2b6cb0);color:white;padding:24px 32px;border-radius:12px 12px 0 0">
          <h1 style="margin:0;font-size:22px">LicitAlertas - Reporte Diario</h1>
          <p style="margin:6px 0 0;opacity:0.85;font-size:14px">{fecha} | {len(convocatorias)} convocatorias activas</p>
          <span style="background:{badge_fuente};color:white;padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700">{label_fuente}</span>
        </div>
        <div style="background:white;padding:24px 32px;border-radius:0 0 12px 12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
          {seccion("URGENTES - Vencen en 3 dias o menos", urgentes, "#e53e3e", "URGENTE")}
          {seccion("PROXIMAS - Vencen en 10 dias o menos", proximas, "#d69e2e", "PROXIMO")}
          {seccion("NORMALES - Mas de 10 dias", normales[:10], "#38a169", "NORMAL")}
        </div>
      </div>
    </body></html>"""

def enviar_email(convocatorias, fecha, fuente="OECE API"):
    if not SENDGRID_API_KEY or not EMAIL_USER or not EMAIL_DESTINO:
        print("Credenciales no configuradas, omitiendo envio.")
        return

    urgentes = len([c for c in convocatorias if c["urg"] == "urgente"])
    asunto = f"LicitAlertas {fecha} - {len(convocatorias)} convocatorias"
    if urgentes > 0:
        asunto = f"LicitAlertas {fecha} - {urgentes} URGENTES + {len(convocatorias)} total"
    if "respaldo" in fuente.lower():
        asunto += " [RESPALDO]"

    html = generar_email_html(convocatorias, fecha, fuente)

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "personalizations": [{"to": [{"email": EMAIL_DESTINO}]}],
            "from": {"email": EMAIL_USER},
            "subject": asunto,
            "content": [{"type": "text/html", "value": html}]
        }
    )
    if response.status_code == 202:
        print(f"Email enviado a {EMAIL_DESTINO}")
    else:
        print(f"Error enviando email: {response.status_code} {response.text}")

def main():
    fecha = datetime.now().strftime("%d/%m/%Y")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Iniciando scraper LicitAlertas...")

    fuente = "OECE API"
    data = obtener_convocatorias()
    convocatorias = procesar_datos(data) if data else []

    # Filtrar solo activas (no vencidas)
    convocatorias_activas = []
    for c in convocatorias:
        dias = dias_restantes(c.get("fecha_vencimiento", ""))
        if dias >= 0:
            convocatorias_activas.append(c)

    print(f"Convocatorias activas (no vencidas): {len(convocatorias_activas)}")

    if not convocatorias_activas:
        print("Sin datos reales activos, usando respaldo...")
        convocatorias_activas = datos_respaldo()
        fuente = "Datos de respaldo"

    for c in convocatorias_activas:
        c["dias"] = dias_restantes(c.get("fecha_vencimiento", ""))
        c["urg"] = urgencia(c["dias"])

    output = {
        "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(convocatorias_activas),
        "fuente": fuente,
        "convocatorias": convocatorias_activas
    }
    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"datos.json guardado: {len(convocatorias_activas)} convocatorias ({fuente})")

    enviar_email(convocatorias_activas, fecha, fuente)
    print("Proceso completado.")

if __name__ == "__main__":
    main()

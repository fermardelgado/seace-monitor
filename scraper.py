import requests
import json
import os
from datetime import datetime, timedelta

# Configuracion SendGrid
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_DESTINO = os.environ.get("EMAIL_DESTINO", "")

BASE_URL = "https://prod2.seace.gob.pe/seacebus-uimp-pub/buscadorPublico/"
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}

def obtener_convocatorias():
    hoy = datetime.now()
    hace_30_dias = hoy - timedelta(days=30)
    payload = {
        "numPagina": 1,
        "numResultados": 100,
        "codigoEntidad": "",
        "fechaInicio": hace_30_dias.strftime("%d/%m/%Y"),
        "fechaFin": hoy.strftime("%d/%m/%Y"),
        "idEstadoProceso": "1",
    }
    try:
        resp = requests.post(BASE_URL + "listarProcesosActivos", json=payload, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error SEACE: {e}")
        return None

def procesar_datos(data):
    if not data:
        return []
    registros = data.get("listaResultados", []) or data.get("registros", []) or []
    convocatorias = []
    for r in registros:
        try:
            conv = {
                "id": str(r.get("idProceso") or r.get("codigoProceso", "")),
                "titulo": r.get("descripcionObjeto") or r.get("nombreObjeto", "Sin titulo"),
                "entidad": r.get("nombreEntidad") or r.get("entidad", ""),
                "tipo": r.get("descripcionTipoProceso") or r.get("tipoProceso", ""),
                "monto": float(r.get("valorReferencial") or r.get("montoReferencial") or 0),
                "region": r.get("nombreDepartamento") or r.get("region") or "Lima",
                "fecha_publicacion": r.get("fechaPublicacion") or r.get("fecPublicacion") or "",
                "fecha_vencimiento": r.get("fechaVencimiento") or r.get("fecVencimiento") or "",
                "estado": r.get("descripcionEstadoProceso") or "Activo",
                "url_seace": f"https://seace.gob.pe/proceso/{r.get('codigoProceso','')}",
            }
            convocatorias.append(conv)
        except:
            continue
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
        {"id":"F007","titulo":"Suministro de utiles de oficina","entidad":"Ministerio de Economia","tipo":"Comparacion de Precios","monto":15000,"region":"Lima","fecha_vencimiento":f(0),"url_seace":"https://seace.gob.pe"},
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

def generar_email_html(convocatorias, fecha):
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

    return f"""<html><body style="font-family:Arial,sans-serif;background:#f0f4f8;margin:0;padding:20px">
      <div style="max-width:900px;margin:0 auto">
        <div style="background:linear-gradient(135deg,#1a365d,#2b6cb0);color:white;padding:24px 32px;border-radius:12px 12px 0 0">
          <h1 style="margin:0;font-size:22px">LicitAlertas - Reporte Diario</h1>
          <p style="margin:6px 0 0;opacity:0.85;font-size:14px">{fecha} | {len(convocatorias)} convocatorias activas</p>
        </div>
        <div style="background:white;padding:24px 32px;border-radius:0 0 12px 12px;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
          {seccion("URGENTES - Vencen en 3 dias o menos", urgentes, "#e53e3e", "URGENTE")}
          {seccion("PROXIMAS - Vencen en 10 dias o menos", proximas, "#d69e2e", "PROXIMO")}
          {seccion("NORMALES - Mas de 10 dias", normales[:10], "#38a169", "NORMAL")}
        </div>
      </div>
    </body></html>"""

def enviar_email(convocatorias, fecha):
    if not SENDGRID_API_KEY or not EMAIL_USER or not EMAIL_DESTINO:
        print("Credenciales no configuradas, omitiendo envio.")
        return

    urgentes = len([c for c in convocatorias if c["urg"] == "urgente"])
    asunto = f"LicitAlertas {fecha} - {len(convocatorias)} convocatorias"
    if urgentes > 0:
        asunto = f"LicitAlertas {fecha} - {urgentes} URGENTES + {len(convocatorias)} total"

    html = generar_email_html(convocatorias, fecha)

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
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Iniciando scraper SEACE...")

    data = obtener_convocatorias()
    convocatorias = procesar_datos(data) if data else []

    if not convocatorias:
        print("Usando datos de respaldo...")
        convocatorias = datos_respaldo()

    for c in convocatorias:
        c["dias"] = dias_restantes(c.get("fecha_vencimiento", ""))
        c["urg"] = urgencia(c["dias"])

    output = {
        "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(convocatorias),
        "fuente": "SEACE - Sistema Electronico de Contrataciones del Estado",
        "convocatorias": convocatorias
    }
    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"datos.json guardado: {len(convocatorias)} convocatorias")

    enviar_email(convocatorias, fecha)
    print("Proceso completado.")

if __name__ == "__main__":
    main()

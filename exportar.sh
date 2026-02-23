#!/bin/bash

RUTA="/var/waps/sitios-personales/gestor_de_document_cryptogacicos_QR"
SALIDA="$RUTA/proyecto.txt"

echo "📂 Leyendo desde: $RUTA"
echo "📝 Exportando a: $SALIDA"
echo "🚫 Ignorando carpeta: static"
echo "----------------------------------"

> "$SALIDA"
COUNT=0

while IFS= read -r archivo; do
    echo "########################################" >> "$SALIDA"
    echo "# ARCHIVO: $archivo" >> "$SALIDA"
    echo "########################################" >> "$SALIDA"
    echo "" >> "$SALIDA"
    cat "$archivo" >> "$SALIDA"
    echo -e "\n\n" >> "$SALIDA"
    COUNT=$((COUNT + 1))
done < <( find "$RUTA" -type d -name "static" -prune -o -type f \( -name "*.py" -o -name "*.html" \))

echo "✅ Archivos exportados: $COUNT"

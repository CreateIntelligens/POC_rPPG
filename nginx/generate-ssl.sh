#!/bin/sh

# SSL憑證生成腳本
# 這個腳本會在nginx容器啟動時自動執行

SSL_DIR="/etc/nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

echo "🔐 Checking SSL certificates..."

# 檢查SSL目錄是否存在
if [ ! -d "$SSL_DIR" ]; then
    echo "📁 Creating SSL directory: $SSL_DIR"
    mkdir -p "$SSL_DIR"
fi

# 檢查憑證是否已存在且有效
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    # 檢查憑證是否即將過期（30天內）
    if openssl x509 -checkend 2592000 -noout -in "$CERT_FILE" >/dev/null 2>&1; then
        echo "✅ SSL certificate exists and is valid for at least 30 days"
        exit 0
    else
        echo "⚠️  SSL certificate exists but expires soon, regenerating..."
    fi
else
    echo "🔨 SSL certificate not found, generating new one..."
fi

# 安裝 openssl（如果尚未安裝）
if ! command -v openssl >/dev/null 2>&1; then
    echo "📦 Installing openssl..."
    apk add --no-cache openssl
fi

# 生成新的SSL憑證
echo "🔧 Generating self-signed SSL certificate..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=TW/ST=Taiwan/L=Taipei/O=VitalLens/OU=Development/CN=localhost/emailAddress=dev@localhost" \
    2>/dev/null

if [ $? -eq 0 ]; then
    # 設定正確的權限
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"

    echo "✅ SSL certificate generated successfully!"
    echo "📄 Certificate: $CERT_FILE"
    echo "🔑 Private key: $KEY_FILE"

    # 顯示憑證資訊
    echo "📋 Certificate details:"
    openssl x509 -in "$CERT_FILE" -text -noout | grep -E "(Subject:|Not After)" | sed 's/^[[:space:]]*/  /'
else
    echo "❌ Failed to generate SSL certificate"
    exit 1
fi
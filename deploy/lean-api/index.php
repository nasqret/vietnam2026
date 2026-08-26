<?php
/**
 * Same-origin, allowlisted gateway to Hydra's loopback-only Lean service.
 *
 * Faculty hosting permits PHP but no persistent daemons. An operator opens an
 * SSH reverse tunnel from the checked local repository; this gateway forwards
 * only /api/lean-strands requests through the faculty-side loopback listener.
 * Neither repository files nor arbitrary upstream hosts are ever exposed.
 */
declare(strict_types=1);

@ini_set('display_errors', '0');
@ini_set('log_errors', '1');
@ini_set('error_log', dirname(__DIR__, 3) . '/.hydra-lean-mailbox/php-errors.log');

const HYDRA_API_PREFIX = '/api/lean-strands';
const HYDRA_FACULTY_HOST = 'bnaskrecki.faculty.wmi.amu.edu.pl';
const HYDRA_TUNNEL_HOST = '127.0.0.1';
const HYDRA_TUNNEL_PORT = 18787;
const HYDRA_SERVICE_HOST = '127.0.0.1:8787';
const HYDRA_MAX_REQUEST_BYTES = 16384;
const HYDRA_MAX_JSON_BYTES = 3145728;
const HYDRA_MAX_RESPONSE_BYTES = 67108864;
const HYDRA_MAX_HEADER_BYTES = 24576;
const HYDRA_JOB_SCHEMA = 'peano-lean-strand-service-v1';
const HYDRA_MAILBOX_SCHEMA = 'peano-lean-mailbox-v1';

function hydra_fail(int $status, string $message): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store, max-age=0');
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: same-origin');
    header('Cross-Origin-Resource-Policy: same-origin');
    echo json_encode(
        ['schema' => HYDRA_JOB_SCHEMA, 'error' => $message],
        JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
    ), "\n";
    exit;
}

/** Exchange one bounded request through the owner's private shared NFS home. */
function hydra_mailbox_exchange(string $method, string $target, string $body)
{
    $directory = dirname(__DIR__, 3) . '/.hydra-lean-mailbox';
    $owner = @fileowner(__FILE__);
    $permissions = @fileperms($directory);
    if (
        !is_dir($directory)
        || is_link($directory)
        || !is_int($owner)
        || @fileowner($directory) !== $owner
        || !is_int($permissions)
        || ($permissions & 0777) !== 0700
    ) {
        return null;
    }
    try {
        $identifier = bin2hex(random_bytes(16));
    } catch (Throwable $error) {
        return null;
    }
    $request = $directory . '/' . $identifier . '.request.json';
    $temporary = $request . '.tmp';
    $metadata = $directory . '/' . $identifier . '.response.json';
    $payload = $directory . '/' . $identifier . '.body';
    $message = json_encode(
        [
            'schema' => HYDRA_MAILBOX_SCHEMA,
            'id' => $identifier,
            'method' => $method,
            'target' => $target,
            'body_base64' => base64_encode($body),
        ],
        JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
    );
    if (!is_string($message) || strlen($message) > HYDRA_MAX_REQUEST_BYTES * 2) {
        return null;
    }
    $handle = @fopen($temporary, 'xb');
    if (!is_resource($handle)) {
        return null;
    }
    @chmod($temporary, 0600);
    $written = fwrite($handle, $message . "\n");
    fflush($handle);
    fclose($handle);
    if ($written !== strlen($message) + 1 || !@rename($temporary, $request)) {
        @unlink($temporary);
        return null;
    }

    $deadline = microtime(true) + 25.0;
    $poll = 0;
    while (microtime(true) < $deadline) {
        if (($poll++ % 4) === 0) {
            @touch($directory);
            clearstatcache(true, $directory);
        }
        clearstatcache(true, $metadata);
        if (!is_file($metadata) || is_link($metadata)) {
            usleep(50000);
            continue;
        }
        if (@fileowner($metadata) !== $owner || ((int) @fileperms($metadata) & 0777) !== 0600) {
            error_log('Hydra private mailbox rejected response ownership or permissions.');
            return null;
        }
        $size = @filesize($metadata);
        if (!is_int($size) || $size < 2 || $size > HYDRA_MAX_HEADER_BYTES) {
            error_log('Hydra private mailbox rejected response metadata size.');
            @unlink($metadata);
            @unlink($payload);
            return null;
        }
        $encoded = @file_get_contents($metadata, false, null, 0, HYDRA_MAX_HEADER_BYTES + 1);
        $record = is_string($encoded) ? json_decode($encoded, true) : null;
        if (
            !is_array($record)
            || ($record['schema'] ?? null) !== HYDRA_MAILBOX_SCHEMA
            || ($record['id'] ?? null) !== $identifier
            || !is_int($record['status'] ?? null)
            || $record['status'] < 100
            || $record['status'] > 599
            || !is_array($record['headers'] ?? null)
            || !is_string($record['headers']['content_type'] ?? null)
            || !is_int($record['headers']['content_length'] ?? null)
            || $record['headers']['content_length'] < 0
            || $record['headers']['content_length'] > HYDRA_MAX_RESPONSE_BYTES
            || !is_int($record['body_bytes'] ?? null)
            || $record['body_bytes'] < 0
            || $record['body_bytes'] > HYDRA_MAX_RESPONSE_BYTES
            || (
                $method === 'HEAD'
                    ? $record['body_bytes'] !== 0
                    : $record['body_bytes'] !== $record['headers']['content_length']
            )
            || !is_string($record['body_sha256'] ?? null)
            || !preg_match('/^[0-9a-f]{64}$/D', $record['body_sha256'])
        ) {
            error_log('Hydra private mailbox rejected its response envelope.');
            @unlink($metadata);
            @unlink($payload);
            return null;
        }
        clearstatcache(true, $payload);
        if (
            !is_file($payload)
            || is_link($payload)
            || @fileowner($payload) !== $owner
            || ((int) @fileperms($payload) & 0777) !== 0600
            || @filesize($payload) !== $record['body_bytes']
            || !hash_equals($record['body_sha256'], (string) @hash_file('sha256', $payload))
        ) {
            error_log('Hydra private mailbox rejected response body ownership, size, or digest.');
            @unlink($metadata);
            @unlink($payload);
            return null;
        }
        $response = @fopen($payload, 'rb');
        if (!is_resource($response)) {
            error_log('Hydra private mailbox could not open its checked response body.');
            @unlink($metadata);
            @unlink($payload);
            return null;
        }
        @unlink($metadata);
        @unlink($payload);
        return ['stream' => $response, 'status' => $record['status'], 'headers' => $record['headers']];
    }
    error_log('Hydra private mailbox response exceeded its bounded wait.');
    @unlink($request);
    return null;
}

$method = $_SERVER['REQUEST_METHOD'] ?? '';
if (!in_array($method, ['GET', 'HEAD', 'POST', 'DELETE'], true)) {
    header('Allow: GET, HEAD, POST, DELETE');
    hydra_fail(405, 'Unsupported Lean proof gateway method.');
}

$host = strtolower($_SERVER['HTTP_HOST'] ?? '');
if ($host !== HYDRA_FACULTY_HOST) {
    hydra_fail(421, 'This Lean proof gateway accepts only its faculty hostname.');
}

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && $origin !== 'https://' . HYDRA_FACULTY_HOST) {
    hydra_fail(403, 'Cross-origin Lean proof requests are forbidden.');
}
if (
    in_array($method, ['POST', 'DELETE'], true)
    && isset($_SERVER['HTTP_SEC_FETCH_SITE'])
    && !in_array($_SERVER['HTTP_SEC_FETCH_SITE'], ['same-origin', 'none'], true)
) {
    hydra_fail(403, 'Cross-site Lean proof mutations are forbidden.');
}

$rawTarget = $_SERVER['REQUEST_URI'] ?? '';
if (
    $rawTarget === ''
    || strlen($rawTarget) > 4096
    || preg_match('/[^\x21-\x7e]/D', $rawTarget)
) {
    hydra_fail(400, 'The Lean proof request target is invalid.');
}
$path = parse_url($rawTarget, PHP_URL_PATH);
if (
    !is_string($path)
    || !preg_match(
        '#^/api/lean-strands(?:/(?:config|health|jobs(?:/[0-9a-f]{32}(?:/(?:download|events))?)?))?$#D',
        $path
    )
) {
    hydra_fail(404, 'Unknown Lean proof gateway endpoint.');
}
if (substr($path, -7) === '/events') {
    hydra_fail(405, 'Use bounded job-status polling on the public Lean gateway.');
}
if ($method === 'POST' && $path !== HYDRA_API_PREFIX . '/jobs') {
    hydra_fail(405, 'Only checked-theorem job creation accepts POST.');
}
if (
    $method === 'DELETE'
    && !preg_match('#^/api/lean-strands/jobs/[0-9a-f]{32}$#D', $path)
) {
    hydra_fail(405, 'Only one opaque proof-job identifier accepts DELETE.');
}

$query = parse_url($rawTarget, PHP_URL_QUERY);
$download = substr($path, -9) === '/download';
if ($download) {
    if (!is_string($query) || !preg_match('/^format=(?:lean|zip)$/D', $query)) {
        hydra_fail(400, 'Proof downloads require exactly one reviewed lean or zip format.');
    }
} elseif ($query !== null && $query !== false && $query !== '') {
    hydra_fail(400, 'Lean proof routes do not accept arbitrary query parameters.');
}

$body = '';
if ($method === 'POST') {
    $contentType = strtolower(trim(explode(';', $_SERVER['CONTENT_TYPE'] ?? '')[0]));
    $rawLength = $_SERVER['CONTENT_LENGTH'] ?? '';
    if ($contentType !== 'application/json') {
        hydra_fail(415, 'Lean proof jobs require application/json.');
    }
    if (!preg_match('/^[0-9]{1,5}$/D', $rawLength)) {
        hydra_fail(400, 'Lean proof jobs require an exact bounded Content-Length.');
    }
    $length = (int) $rawLength;
    if ($length < 1 || $length > HYDRA_MAX_REQUEST_BYTES) {
        hydra_fail(413, 'The Lean proof job exceeds its request-size limit.');
    }
    $received = file_get_contents('php://input', false, null, 0, $length + 1);
    if (!is_string($received) || strlen($received) !== $length) {
        hydra_fail(400, 'The Lean proof request body has an inconsistent length.');
    }
    $decoded = json_decode($received);
    if (!is_object($decoded) || json_last_error() !== JSON_ERROR_NONE) {
        hydra_fail(400, 'The Lean proof request must be one valid JSON object.');
    }
    $body = $received;
}

$errorCode = 0;
$errorMessage = '';
$upstream = @stream_socket_client(
    'tcp://' . HYDRA_TUNNEL_HOST . ':' . HYDRA_TUNNEL_PORT,
    $errorCode,
    $errorMessage,
    2.0,
    STREAM_CLIENT_CONNECT
);
$mailbox = null;
if (!is_resource($upstream)) {
    try {
        $mailbox = hydra_mailbox_exchange($method, $rawTarget, $body);
    } catch (Throwable $error) {
        $mailbox = null;
    }
    if ($mailbox === null) {
        hydra_fail(
            503,
            'The public Lean proof worker is offline. The operator can start it with make lean-public.'
        );
    }
    $upstream = $mailbox['stream'];
    $status = $mailbox['status'];
    $upstreamHeaders = [
        'content-type' => $mailbox['headers']['content_type'],
        'content-length' => (string) $mailbox['headers']['content_length'],
    ];
    if (isset($mailbox['headers']['content_disposition'])) {
        $upstreamHeaders['content-disposition'] = $mailbox['headers']['content_disposition'];
    }
} else {
    stream_set_timeout($upstream, 30);

    $request = $method . ' ' . $rawTarget . " HTTP/1.1\r\n"
        . 'Host: ' . HYDRA_SERVICE_HOST . "\r\n"
        . "Connection: close\r\n";
    if ($method === 'POST') {
        $request .= "Content-Type: application/json\r\n"
            . 'Content-Length: ' . strlen($body) . "\r\n";
    }
    $request .= "\r\n" . $body;
    $written = 0;
    while ($written < strlen($request)) {
        $count = @fwrite($upstream, substr($request, $written));
        if ($count === false || $count === 0) {
            fclose($upstream);
            hydra_fail(502, 'The bounded Lean proof worker did not accept the request.');
        }
        $written += $count;
    }

    $statusLine = fgets($upstream, 8193);
    if (
        !is_string($statusLine)
        || !preg_match('#^HTTP/1\.[01] ([1-5][0-9]{2})(?: [^\r\n]*)?\r?\n$#D', $statusLine, $match)
    ) {
        fclose($upstream);
        hydra_fail(502, 'The Lean proof worker returned an invalid HTTP status.');
    }
    $status = (int) $match[1];
    $headerBytes = strlen($statusLine);
    $upstreamHeaders = [];
    while (true) {
        $line = fgets($upstream, 8193);
        if (!is_string($line)) {
            fclose($upstream);
            hydra_fail(502, 'The Lean proof worker returned incomplete HTTP headers.');
        }
        $headerBytes += strlen($line);
        if ($headerBytes > HYDRA_MAX_HEADER_BYTES) {
            fclose($upstream);
            hydra_fail(502, 'The Lean proof worker exceeded its bounded header budget.');
        }
        if ($line === "\r\n" || $line === "\n") {
            break;
        }
        if (!preg_match('/^([A-Za-z0-9-]+):[ \t]*([^\r\n]*)\r?\n$/D', $line, $header)) {
            fclose($upstream);
            hydra_fail(502, 'The Lean proof worker returned an unsafe HTTP header.');
        }
        $name = strtolower($header[1]);
        if (isset($upstreamHeaders[$name])) {
            fclose($upstream);
            hydra_fail(502, 'The Lean proof worker returned a duplicate HTTP header.');
        }
        $upstreamHeaders[$name] = $header[2];
    }
}

$declared = $upstreamHeaders['content-length'] ?? '';
if (!preg_match('/^[0-9]{1,8}$/D', $declared)) {
    fclose($upstream);
    hydra_fail(502, 'The Lean proof worker omitted its exact response length.');
}
$remaining = (int) $declared;
$responseLimit = $download ? HYDRA_MAX_RESPONSE_BYTES : HYDRA_MAX_JSON_BYTES;
if ($remaining > $responseLimit) {
    fclose($upstream);
    hydra_fail(502, 'The Lean proof worker exceeded its response-size limit.');
}
$kind = $upstreamHeaders['content-type'] ?? '';
if (
    !preg_match(
        '#^(?:application/json(?:; charset=utf-8)?|application/zip|text/plain; charset=utf-8)$#Di',
        $kind
    )
) {
    fclose($upstream);
    hydra_fail(502, 'The Lean proof worker returned an unsupported response type.');
}

http_response_code($status);
header('Content-Type: ' . $kind);
header('Content-Length: ' . $remaining);
header('Cache-Control: no-store, max-age=0');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header('Cross-Origin-Resource-Policy: same-origin');
if (isset($upstreamHeaders['content-disposition'])) {
    $disposition = $upstreamHeaders['content-disposition'];
    if (!preg_match('/^attachment; filename="[A-Za-z0-9_.-]{1,128}"$/D', $disposition)) {
        fclose($upstream);
        hydra_fail(502, 'The Lean proof worker supplied an unsafe download filename.');
    }
    header('Content-Disposition: ' . $disposition);
}
if ($method === 'HEAD') {
    fclose($upstream);
    exit;
}
while ($remaining > 0) {
    $chunk = fread($upstream, min(65536, $remaining));
    if (!is_string($chunk) || $chunk === '') {
        fclose($upstream);
        exit;
    }
    $remaining -= strlen($chunk);
    echo $chunk;
}
fclose($upstream);

<?php
/**
 * Read-only delivery of manifest-authorized Peano bytes, compatible with PHP 7.0+.
 * No sessions, uploads, writes, external requests, commands, or proof execution.
 * The application/vendor manifests authorize files, not mathematical claims.
 */
declare(strict_types=1);

namespace PeanoDelivery;

const MAX_FILE = 67108864;
const MAX_MANIFEST = 1048576;
const MAX_HEADER = 8192;
const VENDOR_CANONICAL = 'v-85fb3352e49c';
// The historical locale-dependent name has exactly the same 18 source files.
const LEGACY_VENDOR = 'v-2eaf25dc3894';

final class DeliveryError extends \RuntimeException
{
    public $status;
    public $headers;
    public function __construct(int $status, array $headers = [])
    {
        parent::__construct('Peano delivery request could not be served.');
        $this->status = $status;
        $this->headers = $headers;
    }
}

function valid_path(string $path): bool
{
    if (strlen($path) > 2048 || substr_count($path, '/') > 24) {
        return false;
    }
    return preg_match('~\A[A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.-]*)*\z~D', $path) === 1;
}

/** Inspect each component; neither symlinks nor shared-writable files are served. */
function checked_path(string $root, string $relative, bool $optional = false)
{
    if (!valid_path(ltrim($relative, '.')) || strpos($relative, '..') !== false) {
        throw new DeliveryError(503);
    }
    $path = $root;
    $parts = explode('/', $relative);
    $owner = fileowner(__FILE__);
    foreach (array_merge([''], $parts) as $index => $part) {
        if ($index > 0) {
            $path .= '/' . $part;
        }
        clearstatcache(true, $path);
        $stat = @lstat($path);
        if ($stat === false) {
            if ($optional) {
                return null;
            }
            throw new DeliveryError(503);
        }
        $kind = $stat['mode'] & 0170000;
        $expected = $index === count($parts) ? 0100000 : 0040000;
        if ($kind !== $expected || ($stat['mode'] & 0022) !== 0 || $stat['uid'] !== $owner) {
            throw new DeliveryError(503);
        }
    }
    return $path;
}

/** Hash the same bounded file descriptor that will subsequently be streamed. */
function open_checked(string $root, string $relative, $expected, int $limit = MAX_FILE): array
{
    $path = checked_path($root, $relative);
    $before = lstat($path);
    $stream = @fopen($path, 'rb');
    if ($stream === false) {
        throw new DeliveryError(503);
    }
    $stat = fstat($stream);
    if ($stat === false || $stat['size'] < 0 || $stat['size'] > $limit
        || $stat['ino'] !== $before['ino'] || $stat['dev'] !== $before['dev']
        || ($stat['mode'] & 0170000) !== 0100000) {
        fclose($stream);
        throw new DeliveryError(503);
    }
    $hash = hash_init('sha256');
    $read = hash_update_stream($hash, $stream, $stat['size']);
    $digest = hash_final($hash);
    if ($read !== $stat['size'] || ($expected !== null && !hash_equals($expected, $digest))
        || !rewind($stream)) {
        fclose($stream);
        throw new DeliveryError(503);
    }
    return ['stream' => $stream, 'size' => $stat['size'], 'sha256' => $digest,
        'mtime' => min($stat['mtime'], time())];
}

function read_small(string $root, string $relative, int $limit): string
{
    $file = open_checked($root, $relative, null, $limit);
    $text = stream_get_contents($file['stream']);
    fclose($file['stream']);
    if (!is_string($text) || strlen($text) !== $file['size']) {
        throw new DeliveryError(503);
    }
    return $text;
}

function manifest(string $text): array
{
    if ($text === '' || substr($text, -1) !== "\n") {
        throw new DeliveryError(503);
    }
    $rows = [];
    foreach (explode("\n", rtrim($text, "\n")) as $line) {
        if (preg_match('~\A([0-9a-f]{64})  (?:\./)?(.+)\z~D', $line, $match) !== 1
            || !valid_path($match[2]) || isset($rows[$match[2]]) || count($rows) >= 8192) {
            throw new DeliveryError(503);
        }
        $rows[$match[2]] = $match[1];
    }
    return $rows;
}

function media_type(string $path): array
{
    $types = [
        'html' => ['text/html; charset=utf-8', true],
        'js' => ['application/javascript; charset=utf-8', true],
        'css' => ['text/css; charset=utf-8', true],
        'json' => ['application/json', true],
        'py' => ['text/plain; charset=utf-8', true],
        'txt' => ['text/plain; charset=utf-8', true],
        'sha256' => ['text/plain; charset=utf-8', true],
        'wasm' => ['application/wasm', true],
        'zip' => ['application/zip', false],
        'woff2' => ['font/woff2', false],
    ];
    $extension = pathinfo($path, PATHINFO_EXTENSION);
    if (!isset($types[$extension])) {
        throw new DeliveryError(404);
    }
    return $types[$extension];
}

/** Resolve only the two Peano mount points and their known public namespaces. */
function resource(string $root, array $server): array
{
    $script = $server['SCRIPT_NAME'] ?? '';
    if (!is_string($script)
        || preg_match('~\A(/peano-lab(?:-next)?/)peano-delivery\.php\z~D', $script, $match) !== 1) {
        throw new DeliveryError(404);
    }
    $uri = $server['REQUEST_URI'] ?? '';
    if (!is_string($uri) || strlen($uri) > 4096) {
        throw new DeliveryError(414);
    }
    $path = explode('?', $uri, 2)[0];
    if (substr($path, 0, strlen($match[1])) !== $match[1]) {
        throw new DeliveryError(404);
    }
    $path = substr($path, strlen($match[1]));
    $path = $path === '' ? 'index.html' : $path;
    // All published paths are ASCII. Reject escaped separators and double decoding.
    if (!valid_path($path)) {
        throw new DeliveryError(404);
    }
    $media = media_type($path);
    $expected = null;
    $cache = 'no-cache';
    $limit = MAX_FILE;
    if ($path === 'index.html') {
        $cache = 'no-store, no-cache, must-revalidate, max-age=0';
        $limit = MAX_MANIFEST;
    } elseif ($path === 'vendor/MANIFEST.sha256') {
        $limit = MAX_MANIFEST;
    } elseif (preg_match('~\Areleases/(a-[0-9a-f]{12})/(.+)\z~D', $path, $app) === 1) {
        $name = 'releases/' . $app[1] . '/APP_MANIFEST.sha256';
        if (checked_path($root, $name, true) === null) {
            throw new DeliveryError(404);
        }
        $text = read_small($root, $name, MAX_MANIFEST);
        $hash = hash('sha256', $text);
        if ('a-' . substr($hash, 0, 12) !== $app[1]) {
            throw new DeliveryError(503);
        }
        $rows = manifest($text);
        $expected = $app[2] === 'APP_MANIFEST.sha256' ? $hash : ($rows[$app[2]] ?? null);
        if ($expected === null) {
            throw new DeliveryError(404);
        }
        $cache = 'public, max-age=31536000, immutable';
    } elseif (preg_match('~\Avendor/(?:(v-[0-9a-f]{12})/)?((?:fonts|pyodide|xterm)/.+)\z~D', $path, $vendor) === 1) {
        $id = $vendor[1] === '' ? VENDOR_CANONICAL : $vendor[1];
        $canonical = $id === LEGACY_VENDOR ? VENDOR_CANONICAL : $id;
        $name = '.peano-delivery/vendors/' . $canonical . '.sha256';
        if (checked_path($root, $name, true) === null) {
            throw new DeliveryError(404);
        }
        $text = read_small($root, $name, MAX_MANIFEST);
        if ('v-' . substr(hash('sha256', $text), 0, 12) !== $canonical) {
            throw new DeliveryError(503);
        }
        $expected = manifest($text)[$vendor[2]] ?? null;
        if ($expected === null) {
            throw new DeliveryError(404);
        }
        if ($vendor[1] !== '') {
            $cache = 'public, max-age=31536000, immutable';
        }
    } else {
        throw new DeliveryError(404);
    }
    return [open_checked($root, $path, $expected, $limit), $cache, $media];
}

/** q=0 always excludes that coding; duplicate entries take the stricter value. */
function encoding(string $header, bool $gzipAvailable): string
{
    $weights = [];
    foreach (explode(',', strtolower($header)) as $part) {
        if (trim($part) === '') {
            continue;
        }
        if (preg_match('~\A\s*([a-z0-9*_-]+)\s*(?:;\s*q\s*=\s*(0(?:\.[0-9]{0,3})?|1(?:\.0{0,3})?))?\s*\z~D', $part, $m) !== 1) {
            throw new DeliveryError(400);
        }
        $q = isset($m[2]) ? (float)$m[2] : 1.0;
        $weights[$m[1]] = min($weights[$m[1]] ?? 1.0, $q);
    }
    $gzip = $gzipAvailable ? ($weights['gzip'] ?? $weights['*'] ?? 0.0) : 0.0;
    $identity = $weights['identity'] ?? (($weights['*'] ?? 1.0) === 0.0 ? 0.0 : 1.0);
    if ($gzip > 0 && (!isset($weights['identity']) || $gzip >= $identity)) {
        return 'gzip';
    }
    if ($identity > 0) {
        return 'identity';
    }
    throw new DeliveryError(406);
}

function gzip_representation(string $root, array $plain)
{
    $name = '.peano-delivery/gzip/' . $plain['sha256'] . '.json';
    if (checked_path($root, $name, true) === null) {
        return null;
    }
    $meta = json_decode(read_small($root, $name, 2048), true);
    if (!is_array($meta) || ($meta['schema'] ?? '') !== 'peano-gzip-v1'
        || ($meta['plain_sha256'] ?? '') !== $plain['sha256']
        || ($meta['plain_bytes'] ?? -1) !== $plain['size']
        || !is_string($meta['sha256'] ?? null)
        || preg_match('/\A[0-9a-f]{64}\z/D', $meta['sha256']) !== 1
        || !is_int($meta['bytes'] ?? null) || $meta['bytes'] < 0 || $meta['bytes'] > MAX_FILE) {
        throw new DeliveryError(503);
    }
    $file = open_checked($root, '.peano-delivery/gzip/' . $meta['sha256'] . '.gz', $meta['sha256']);
    if ($file['size'] !== $meta['bytes']) {
        fclose($file['stream']);
        throw new DeliveryError(503);
    }
    return $file;
}

function matches_etag(string $header, string $etag, bool $weak): bool
{
    if (trim($header) === '*') {
        return true;
    }
    foreach (explode(',', $header) as $candidate) {
        $candidate = trim($candidate);
        if ($weak && substr($candidate, 0, 2) === 'W/') {
            $candidate = substr($candidate, 2);
        }
        if ($candidate === $etag) {
            return true;
        }
    }
    return false;
}

function http_date(string $value)
{
    if (!preg_match('/\A[A-Za-z]{3}, [0-9]{2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} GMT\z/D', $value)) {
        return null;
    }
    $date = strtotime($value);
    return $date === false ? null : $date;
}

/** Single byte ranges; unsupported units/multipart/malformed fields are ignored. */
function byte_range(string $header, int $size)
{
    if (preg_match('/\Abytes=([0-9]{0,18})-([0-9]{0,18})\z/D', trim($header), $m) !== 1
        || ($m[1] === '' && $m[2] === '')) {
        return null;
    }
    if ($m[1] === '') {
        $length = (int)$m[2];
        $start = max(0, $size - $length);
        $end = $size - 1;
    } else {
        $start = (int)$m[1];
        $end = $m[2] === '' ? $size - 1 : min((int)$m[2], $size - 1);
    }
    if ($size === 0 || $start >= $size || $end < $start) {
        throw new DeliveryError(416, ['Content-Range' => 'bytes */' . $size]);
    }
    return [$start, $end];
}

function failure(int $status, bool $head, array $extra = []): array
{
    $body = 'Peano delivery: HTTP ' . $status . ".\n";
    return ['status' => $status, 'headers' => array_merge([
        'Cache-Control' => 'no-store, max-age=0',
        'Content-Type' => 'text/plain; charset=utf-8',
        'X-Content-Type-Options' => 'nosniff', 'Content-Length' => (string)strlen($body),
    ], $extra), 'body' => $head ? '' : $body, 'stream' => null, 'offset' => 0, 'length' => 0];
}

function prepare(string $root, array $server): array
{
    $stream = null;
    $gzipStream = null;
    $head = ($server['REQUEST_METHOD'] ?? '') === 'HEAD';
    try {
        if (!in_array($server['REQUEST_METHOD'] ?? '', ['GET', 'HEAD'], true)) {
            throw new DeliveryError(405, ['Allow' => 'GET, HEAD']);
        }
        $total = 0;
        foreach (['HTTP_ACCEPT_ENCODING', 'HTTP_RANGE', 'HTTP_IF_RANGE', 'HTTP_IF_MATCH',
            'HTTP_IF_NONE_MATCH', 'HTTP_IF_MODIFIED_SINCE', 'HTTP_IF_UNMODIFIED_SINCE'] as $name) {
            if (isset($server[$name])) {
                if (!is_string($server[$name]) || preg_match('/[\x00-\x08\x0a-\x1f\x7f]/', $server[$name])) {
                    throw new DeliveryError(400);
                }
                $total += strlen($server[$name]);
            }
        }
        if ($total > MAX_HEADER) {
            throw new DeliveryError(431);
        }
        list($file, $cache, $media) = resource($root, $server);
        $stream = $file['stream'];
        $modified = $file['mtime'];
        $gzip = $media[1] ? gzip_representation($root, $file) : null;
        $gzipStream = $gzip === null ? null : $gzip['stream'];
        $coding = encoding($server['HTTP_ACCEPT_ENCODING'] ?? '', $gzip !== null);
        if ($coding === 'gzip') {
            fclose($stream);
            $file = $gzip;
            $stream = $gzipStream;
            $gzipStream = null;
        } elseif (is_resource($gzipStream)) {
            fclose($gzipStream);
            $gzipStream = null;
        }
        $etag = '"' . $file['sha256'] . '-' . $coding . '"';
        $headers = ['Content-Type' => $media[0], 'Cache-Control' => $cache,
            'ETag' => $etag, 'Last-Modified' => gmdate('D, d M Y H:i:s', $modified) . ' GMT',
            'Vary' => 'Accept-Encoding', 'Accept-Ranges' => 'bytes',
            'X-Content-Type-Options' => 'nosniff'];
        if ($coding === 'gzip') {
            $headers['Content-Encoding'] = 'gzip';
        }
        if (strpos($cache, 'no-store') !== false) {
            $headers['Pragma'] = 'no-cache';
            $headers['Expires'] = '0';
        }
        if (isset($server['HTTP_IF_MATCH'])) {
            if (!matches_etag($server['HTTP_IF_MATCH'], $etag, false)) {
                throw new DeliveryError(412);
            }
        } elseif (isset($server['HTTP_IF_UNMODIFIED_SINCE'])) {
            $date = http_date($server['HTTP_IF_UNMODIFIED_SINCE']);
            if ($date !== null && $modified > $date) {
                throw new DeliveryError(412);
            }
        }
        $notModified = isset($server['HTTP_IF_NONE_MATCH'])
            ? matches_etag($server['HTTP_IF_NONE_MATCH'], $etag, true)
            : (($date = http_date($server['HTTP_IF_MODIFIED_SINCE'] ?? '')) !== null && $modified <= $date);
        $status = $notModified ? 304 : 200;
        $offset = 0;
        $length = $file['size'];
        if (!$notModified && !$head && isset($server['HTTP_RANGE'])) {
            $ifRange = $server['HTTP_IF_RANGE'] ?? $etag;
            $date = http_date($ifRange);
            if ($ifRange === $etag || ($date !== null && $date === $modified)) {
                $range = byte_range($server['HTTP_RANGE'], $file['size']);
                if ($range !== null) {
                    list($offset, $end) = $range;
                    $length = $end - $offset + 1;
                    $status = 206;
                    $headers['Content-Range'] = 'bytes ' . $offset . '-' . $end . '/' . $file['size'];
                }
            }
        }
        if (!$notModified) {
            $headers['Content-Length'] = (string)$length;
        }
        if ($notModified || $head) {
            fclose($stream);
            $stream = null;
            $length = 0;
        }
        return ['status' => $status, 'headers' => $headers, 'body' => '',
            'stream' => $stream, 'offset' => $offset, 'length' => $length];
    } catch (DeliveryError $error) {
        if (is_resource($stream)) { fclose($stream); }
        if (is_resource($gzipStream)) { fclose($gzipStream); }
        return failure($error->status, $head, $error->headers);
    } catch (\Throwable $error) {
        if (is_resource($stream)) { fclose($stream); }
        if (is_resource($gzipStream)) { fclose($gzipStream); }
        return failure(503, $head);
    }
}

function emit(array $response)
{
    http_response_code($response['status']);
    foreach ($response['headers'] as $name => $value) {
        header($name . ': ' . $value, true);
    }
    echo $response['body'];
    if (is_resource($response['stream'])) {
        $stream = $response['stream'];
        if (fseek($stream, $response['offset']) === 0) {
            $left = $response['length'];
            while ($left > 0 && !connection_aborted()) {
                $chunk = fread($stream, min(65536, $left));
                if ($chunk === false || $chunk === '') { break; }
                echo $chunk;
                $left -= strlen($chunk);
            }
        }
        fclose($stream);
    }
}

// CLI inclusion exposes the same pure request/response logic to the test suite.
if (PHP_SAPI !== 'cli') {
    @ini_set('display_errors', '0');
    @ini_set('zlib.output_compression', '0');
    @ini_set('output_buffering', '0');
    if (function_exists('apache_setenv')) {
        apache_setenv('no-gzip', '1');
        apache_setenv('no-brotli', '1');
    }
    while (ob_get_level() > 0) {
        if (!@ob_end_clean()) { break; }
    }
    header_remove('X-Powered-By');
    emit(prepare(__DIR__, $_SERVER));
}

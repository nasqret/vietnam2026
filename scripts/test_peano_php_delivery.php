<?php
/** Portable tests of the exact production request logic; no web server needed. */
declare(strict_types=1);
require $argv[1] ?? __DIR__ . '/../deploy/peano-delivery/peano-delivery.php';

$root = sys_get_temp_dir() . '/peano-delivery-test-' . bin2hex(random_bytes(10));
mkdir($root, 0755);
$passed = [];
$failed = [];

function expect($condition, string $message = 'assertion failed'): void
{
    if (!$condition) { throw new RuntimeException($message); }
}

function put_fixture(string $path, string $data): void
{
    if (!is_dir(dirname($path))) { mkdir(dirname($path), 0755, true); }
    file_put_contents($path, $data);
    chmod($path, 0644);
    touch($path, 1700000000);
    clearstatcache(true, $path);
}

function gzip_fixture(string $root, string $plain): void
{
    $compressed = gzencode($plain, 9);
    $hash = hash('sha256', $compressed);
    put_fixture($root . '/.peano-delivery/gzip/' . $hash . '.gz', $compressed);
    put_fixture($root . '/.peano-delivery/gzip/' . hash('sha256', $plain) . '.json', json_encode([
        'schema' => 'peano-gzip-v1', 'plain_sha256' => hash('sha256', $plain),
        'plain_bytes' => strlen($plain), 'sha256' => $hash, 'bytes' => strlen($compressed),
    ]));
}

function request(string $path, array $headers = [], string $method = 'GET', array $extra = []): array
{
    global $root;
    $server = array_merge(['SCRIPT_NAME' => '/peano-lab-next/peano-delivery.php',
        'REQUEST_URI' => '/peano-lab-next/' . $path, 'REQUEST_METHOD' => $method], $extra);
    foreach ($headers as $key => $value) {
        $server['HTTP_' . str_replace('-', '_', strtoupper($key))] = $value;
    }
    $response = PeanoDelivery\prepare($root, $server);
    if (is_resource($response['stream'])) {
        fseek($response['stream'], $response['offset']);
        $response['body'] = $response['length'] === 0 ? '' : stream_get_contents($response['stream'], $response['length']);
        fclose($response['stream']);
    }
    return $response;
}

function test_case(string $name, callable $callback): void
{
    global $passed, $failed;
    try { $callback(); $passed[] = $name; }
    catch (Throwable $error) { $failed[$name] = get_class($error) . ': ' . $error->getMessage(); }
}

try {
    $index = '<!doctype html><title>Peano</title>Exact entrypoint';
    $worker = str_repeat('const Peano = "exact source";' . "\n", 50);
    $wasm = "\0asm\1\0\0\0" . str_repeat('exact-wasm-byte', 1000);
    $zip = 'PK' . str_repeat('already-compressed', 100);
    $font = 'wOF2' . str_repeat('already-compressed-font', 100);
    $appFiles = ['empty.py' => '', 'py/checker.py' => "print('source, never executed')\n",
        'proof-artifacts/test.json' => '{"checked":true}',
        'unsafe.php' => '<?php file_put_contents("never-created", "unsafe");', 'worker.js' => $worker];
    ksort($appFiles, SORT_STRING);
    $text = '';
    foreach ($appFiles as $path => $data) { $text .= hash('sha256', $data) . '  ' . $path . "\n"; }
    $app = 'a-' . substr(hash('sha256', $text), 0, 12);
    put_fixture($root . '/index.html', $index);
    put_fixture($root . '/releases/' . $app . '/APP_MANIFEST.sha256', $text);
    gzip_fixture($root, $text);
    foreach ($appFiles as $path => $data) {
        put_fixture($root . '/releases/' . $app . '/' . $path, $data);
        gzip_fixture($root, $data);
    }
    $vendorFiles = ['fonts/Inter-400.woff2' => $font, 'pyodide/pyodide.asm.wasm' => $wasm,
        'pyodide/python_stdlib.zip' => $zip];
    $vendorText = '';
    foreach ($vendorFiles as $path => $data) { $vendorText .= hash('sha256', $data) . '  ./' . $path . "\n"; }
    $vendor = 'v-' . substr(hash('sha256', $vendorText), 0, 12);
    put_fixture($root . '/.peano-delivery/vendors/' . $vendor . '.sha256', $vendorText);
    foreach ($vendorFiles as $path => $data) {
        put_fixture($root . '/vendor/' . $vendor . '/' . $path, $data);
        if (substr($path, -5) === '.wasm') { gzip_fixture($root, $data); }
    }
    put_fixture($root . '/vendor/MANIFEST.sha256', $vendorText);
    gzip_fixture($root, $index);
    $workerPath = 'releases/' . $app . '/worker.js';
    $wasmPath = 'vendor/' . $vendor . '/pyodide/pyodide.asm.wasm';
    $manifestPath = 'releases/' . $app . '/APP_MANIFEST.sha256';

    foreach (['', 'index.html', '?cmd=pa%20help', 'index.html?file=../../secret'] as $path) {
        test_case('exact root ' . $path, function () use ($path, $index) {
            $r = request($path);
            expect($r['status'] === 200 && $r['body'] === $index);
            expect(strpos($r['headers']['Cache-Control'], 'no-store') !== false);
            expect($r['headers']['Content-Length'] === (string)strlen($index));
        });
    }
    foreach ([$workerPath, $manifestPath, $wasmPath] as $path) {
        test_case('immutable response ' . $path, function () use ($path) {
            $r = request($path);
            expect($r['status'] === 200);
            expect($r['headers']['Cache-Control'] === 'public, max-age=31536000, immutable');
            expect($r['headers']['Vary'] === 'Accept-Encoding');
        });
    }
    foreach (['' => $index, $workerPath => $worker, $wasmPath => $wasm] as $path => $body) {
        test_case('GET and HEAD ' . $path, function () use ($path, $body) {
            $r = request($path, [], 'HEAD');
            expect($r['status'] === 200 && $r['body'] === '');
            expect($r['headers']['Content-Length'] === (string)strlen($body));
        });
    }
    $encodings = [
        ['', 200, false], ['gzip', 200, true], ['br, gzip', 200, true], ['br;q=0, gzip', 200, true],
        ['GZIP;Q=1.000', 200, true], ['gzip;q=0', 200, false], ['br', 200, false],
        ['gzip;q=0, *;q=1', 200, false], ['*;q=0', 406, false],
        ['gzip;q=0, identity;q=0', 406, false], ['br, identity;q=0', 406, false],
        ['gzip;q=0.5, identity;q=1', 200, false], ['gzip;q=1, identity;q=0', 200, true],
        ['*;q=0, identity;q=1', 200, false], ['gzip;q=1, gzip;q=0', 200, false],
        ['gzip;q=2', 400, false], ['gzip;q=.5', 400, false],
    ];
    foreach ($encodings as [$accept, $status, $encoded]) {
        test_case('encoding ' . $accept, function () use ($accept, $status, $encoded, $wasmPath, $wasm) {
            $r = request($wasmPath, ['Accept-Encoding' => $accept]);
            expect($r['status'] === $status);
            expect(isset($r['headers']['Content-Encoding']) === $encoded);
            if ($status === 200) { expect(($encoded ? gzdecode($r['body']) : $r['body']) === $wasm); }
        });
    }
    foreach (['fonts/Inter-400.woff2' => 'font/woff2', 'pyodide/python_stdlib.zip' => 'application/zip'] as $path => $type) {
        test_case('binary exclusion ' . $path, function () use ($vendor, $path, $type) {
            $r = request('vendor/' . $vendor . '/' . $path, ['Accept-Encoding' => 'br, gzip']);
            expect($r['status'] === 200 && !isset($r['headers']['Content-Encoding']));
            expect($r['headers']['Content-Type'] === $type);
        });
    }
    test_case('correct WASM MIME', function () use ($wasmPath) {
        expect(request($wasmPath)['headers']['Content-Type'] === 'application/wasm');
    });
    test_case('Python is text, not code execution', function () use ($app) {
        $r = request('releases/' . $app . '/py/checker.py');
        expect($r['status'] === 200 && $r['body'] === "print('source, never executed')\n");
        expect($r['headers']['Content-Type'] === 'text/plain; charset=utf-8');
    });
    foreach (['', $workerPath] as $path) {
        foreach (['plain', 'weak', 'list', 'star', 'gzip'] as $variant) {
            test_case('304 policy ' . $variant . ' ' . $path, function () use ($path, $variant) {
                $headers = $variant === 'gzip' ? ['Accept-Encoding' => 'gzip'] : [];
                $first = request($path, $headers);
                $tag = $first['headers']['ETag'];
                $headers['If-None-Match'] = $variant === 'weak' ? 'W/' . $tag
                    : ($variant === 'list' ? '"other", ' . $tag : ($variant === 'star' ? '*' : $tag));
                $r = request($path, $headers);
                expect($r['status'] === 304 && $r['body'] === '');
                expect($r['headers']['Cache-Control'] === $first['headers']['Cache-Control']);
                expect(!isset($r['headers']['Content-Length']));
            });
        }
    }
    test_case('representation-specific ETags', function () use ($workerPath) {
        $a = request($workerPath); $b = request($workerPath, ['Accept-Encoding' => 'gzip']);
        expect($a['headers']['ETag'] !== $b['headers']['ETag']);
        expect(request($workerPath, ['If-None-Match' => $b['headers']['ETag']])['status'] === 200);
    });
    test_case('conditional precedence', function () use ($workerPath) {
        $first = request($workerPath); $tag = $first['headers']['ETag']; $date = $first['headers']['Last-Modified'];
        expect(request($workerPath, ['If-Modified-Since' => $date])['status'] === 304);
        expect(request($workerPath, ['If-None-Match' => '"different"', 'If-Modified-Since' => $date])['status'] === 200);
        expect(request($workerPath, ['If-Match' => 'W/' . $tag])['status'] === 412);
        expect(request($workerPath, ['If-Match' => $tag])['status'] === 200);
        expect(request($workerPath, ['If-Match' => '*'])['status'] === 200);
        expect(request($workerPath, ['If-Unmodified-Since' => 'Mon, 13 Nov 2023 00:00:00 GMT'])['status'] === 412);
        expect(request($workerPath, ['If-Match' => $tag, 'If-Unmodified-Since' => 'Mon, 13 Nov 2023 00:00:00 GMT'])['status'] === 200);
    });
    $ranges = [['bytes=0-0', 206, substr($wasm, 0, 1)], ['bytes=5-', 206, substr($wasm, 5)],
        ['bytes=-7', 206, substr($wasm, -7)], ['bytes=0-999999', 206, $wasm],
        ['bytes=-999999', 206, $wasm], ['bytes=999999-', 416, null], ['bytes=-0', 416, null],
        ['bytes=8-2', 416, null], ['bytes=0-0,2-2', 200, $wasm], ['items=0-0', 200, $wasm],
        ['bytes=oops', 200, $wasm]];
    foreach ($ranges as [$range, $status, $body]) {
        test_case('range ' . $range, function () use ($range, $status, $body, $wasmPath) {
            $r = request($wasmPath, ['Accept-Encoding' => 'identity', 'Range' => $range]);
            expect($r['status'] === $status);
            if ($body !== null) { expect($r['body'] === $body); }
            expect(strpos($r['headers']['Cache-Control'], $status === 416 ? 'no-store' : 'immutable') !== false);
        });
    }
    test_case('HEAD ignores range; conditionals precede range', function () use ($wasmPath, $wasm) {
        $first = request($wasmPath); $tag = $first['headers']['ETag'];
        $r = request($wasmPath, ['Range' => 'bytes=0-0'], 'HEAD');
        expect($r['status'] === 200 && $r['body'] === '' && $r['headers']['Content-Length'] === (string)strlen($wasm));
        expect(request($wasmPath, ['Range' => 'bytes=0-0', 'If-None-Match' => $tag])['status'] === 304);
        expect(request($wasmPath, ['Range' => 'bytes=0-0', 'If-Match' => '"other"'])['status'] === 412);
    });
    test_case('If-Range strong tag and date', function () use ($wasmPath, $wasm) {
        $first = request($wasmPath);
        foreach ([$first['headers']['ETag'], $first['headers']['Last-Modified']] as $validator) {
            expect(request($wasmPath, ['Range' => 'bytes=0-0', 'If-Range' => $validator])['status'] === 206);
        }
        foreach (['"other"', 'W/' . $first['headers']['ETag'], 'Mon, 13 Nov 2023 00:00:00 GMT'] as $validator) {
            $r = request($wasmPath, ['Range' => 'bytes=0-0', 'If-Range' => $validator]);
            expect($r['status'] === 200 && $r['body'] === $wasm);
        }
    });
    test_case('empty files and ranges', function () use ($app) {
        $path = 'releases/' . $app . '/empty.py';
        expect(request($path)['body'] === '');
        expect(request($path, ['Range' => 'bytes=0-0'])['status'] === 416);
    });
    $badPaths = ['missing', '.htaccess', '.peano-delivery/stage.json', 'peano-delivery.php',
        '../index.html', '%2e%2e/index.html', 'releases//worker.js', '/index.html',
        'index.html/extra', 'index.html%00', '%69ndex.html', 'index.html;secret',
        'releases/' . $app . '/unsafe.php', 'releases/' . $app . '/not-manifested.py',
        'releases/a-000000000000/worker.js', 'vendor/v-000000000000/pyodide/pyodide.asm.wasm'];
    foreach ($badPaths as $path) {
        test_case('deny path ' . $path, function () use ($path) {
            $r = request($path);
            expect($r['status'] === 404);
            expect(strpos($r['headers']['Cache-Control'], 'no-store') !== false);
        });
    }
    foreach (['POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'TRACE'] as $method) {
        test_case('read-only method ' . $method, function () use ($method) {
            $r = request('', [], $method);
            expect($r['status'] === 405 && $r['headers']['Allow'] === 'GET, HEAD');
        });
    }
    test_case('mount isolation and query non-authority', function () {
        expect(request('', [], 'GET', ['REQUEST_URI' => '/proofs/index.html'])['status'] === 404);
        expect(request('', [], 'GET', ['SCRIPT_NAME' => '/other/peano-delivery.php'])['status'] === 404);
        expect(request('', [], 'GET', ['SCRIPT_NAME' => '/peano-lab/peano-delivery.php', 'REQUEST_URI' => '/peano-lab/'])['status'] === 200);
    });
    test_case('header and URL budgets', function () {
        expect(request(str_repeat('a', 4100))['status'] === 414);
        expect(request('', ['If-None-Match' => str_repeat('x', 8193)])['status'] === 431);
        expect(request('', ['Accept-Encoding' => "gzip\r\nX-Injected: true"])['status'] === 400);
    });
    test_case('no-store HEAD error', function () {
        $r = request('missing', [], 'HEAD');
        expect($r['status'] === 404 && $r['body'] === '');
    });
    test_case('tampered source fails closed', function () use ($root, $workerPath, $worker) {
        put_fixture($root . '/' . $workerPath, $worker . 'tampered');
        try { expect(request($workerPath)['status'] === 503); }
        finally { put_fixture($root . '/' . $workerPath, $worker); }
    });
    test_case('tampered manifest fails closed', function () use ($root, $manifestPath, $text, $workerPath) {
        put_fixture($root . '/' . $manifestPath, $text . "\n");
        try { expect(request($workerPath)['status'] === 503); }
        finally { put_fixture($root . '/' . $manifestPath, $text); }
    });
    test_case('writable payload fails closed', function () use ($root, $workerPath) {
        chmod($root . '/' . $workerPath, 0666);
        try { expect(request($workerPath)['status'] === 503); }
        finally { chmod($root . '/' . $workerPath, 0644); }
    });
    test_case('symlink payload fails closed', function () use ($root, $workerPath, $worker) {
        unlink($root . '/' . $workerPath);
        symlink($root . '/index.html', $root . '/' . $workerPath);
        try { expect(request($workerPath)['status'] === 503); }
        finally { unlink($root . '/' . $workerPath); put_fixture($root . '/' . $workerPath, $worker); }
    });
    test_case('tampered gzip fails closed', function () use ($root, $worker, $workerPath) {
        $meta = json_decode(file_get_contents($root . '/.peano-delivery/gzip/' . hash('sha256', $worker) . '.json'), true);
        $file = $root . '/.peano-delivery/gzip/' . $meta['sha256'] . '.gz';
        put_fixture($file, 'not the authorized encoding');
        try { expect(request($workerPath, ['Accept-Encoding' => 'gzip'])['status'] === 503); }
        finally { gzip_fixture($root, $worker); }
    });
    test_case('missing gzip uses acceptable identity', function () use ($root, $worker, $workerPath) {
        $path = $root . '/.peano-delivery/gzip/' . hash('sha256', $worker) . '.json';
        unlink($path);
        try {
            $r = request($workerPath, ['Accept-Encoding' => 'gzip']);
            expect($r['status'] === 200 && $r['body'] === $worker && !isset($r['headers']['Content-Encoding']));
            expect(request($workerPath, ['Accept-Encoding' => 'gzip, identity;q=0'])['status'] === 406);
        } finally { gzip_fixture($root, $worker); }
    });
    test_case('new entrypoint changes ETag without stale manifest coupling', function () use ($root, $index) {
        $before = request('');
        put_fixture($root . '/index.html', $index . ' updated');
        try {
            $after = request('', ['If-None-Match' => $before['headers']['ETag']]);
            expect($after['status'] === 200 && $after['body'] === $index . ' updated');
        } finally { put_fixture($root . '/index.html', $index); }
    });
    test_case('duplicate and unsafe manifest rows rejected', function () {
        $hash = str_repeat('a', 64);
        foreach ([$hash . '  worker.js' . "\n" . $hash . '  worker.js' . "\n", $hash . '  ../secret' . "\n"] as $text) {
            try { PeanoDelivery\manifest($text); throw new RuntimeException('invalid manifest accepted'); }
            catch (PeanoDelivery\DeliveryError $error) { expect($error->status === 503); }
        }
    });
    test_case('oversized entrypoint is rejected before reading', function () use ($root, $index) {
        $file = fopen($root . '/index.html', 'wb');
        ftruncate($file, PeanoDelivery\MAX_MANIFEST + 1);
        fclose($file);
        try { expect(request('')['status'] === 503); }
        finally { put_fixture($root . '/index.html', $index); }
    });
    test_case('oversized asset is rejected before hashing', function () use ($root, $workerPath, $worker) {
        $file = fopen($root . '/' . $workerPath, 'wb');
        ftruncate($file, PeanoDelivery\MAX_FILE + 1);
        fclose($file);
        try { expect(request($workerPath)['status'] === 503); }
        finally { put_fixture($root . '/' . $workerPath, $worker); }
    });
    test_case('directory and parent symlink are not served', function () use ($root, $workerPath, $worker, $app) {
        $path = $root . '/' . $workerPath;
        unlink($path); mkdir($path, 0755);
        try { expect(request($workerPath)['status'] === 503); }
        finally { rmdir($path); put_fixture($path, $worker); }
        $directory = $root . '/releases/' . $app;
        rename($directory, $directory . '-saved');
        symlink($directory . '-saved', $directory);
        try { expect(request($workerPath)['status'] === 503); }
        finally { unlink($directory); rename($directory . '-saved', $directory); }
    });
    test_case('encoding metadata cannot relabel another source', function () use ($root, $workerPath, $worker) {
        $path = $root . '/.peano-delivery/gzip/' . hash('sha256', $worker) . '.json';
        $original = file_get_contents($path);
        $meta = json_decode($original, true);
        $meta['plain_sha256'] = str_repeat('0', 64);
        put_fixture($path, json_encode($meta));
        try { expect(request($workerPath, ['Accept-Encoding' => 'gzip'])['status'] === 503); }
        finally { put_fixture($path, $original); }
    });
    foreach (['full', 'range', 'head', 'gzip'] as $variant) {
        test_case('real response emitter ' . $variant, function () use ($root, $workerPath, $worker, $variant) {
            $server = ['REQUEST_METHOD' => $variant === 'head' ? 'HEAD' : 'GET',
                'SCRIPT_NAME' => '/peano-lab-next/peano-delivery.php',
                'REQUEST_URI' => '/peano-lab-next/' . $workerPath];
            if ($variant === 'range') { $server['HTTP_RANGE'] = 'bytes=2-8'; }
            if ($variant === 'gzip') { $server['HTTP_ACCEPT_ENCODING'] = 'gzip'; }
            $response = PeanoDelivery\prepare($root, $server);
            ob_start(); PeanoDelivery\emit($response); $body = ob_get_clean();
            if ($variant === 'gzip') { $body = gzdecode($body); }
            expect($body === ($variant === 'head' ? '' : ($variant === 'range' ? substr($worker, 2, 7) : $worker)));
            expect(!is_resource($response['stream']));
        });
    }
} finally {
    // Only this test's uniquely created temporary fixture tree is removed.
    $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($iterator as $file) {
        if ($file->isDir() && !$file->isLink()) { rmdir($file->getPathname()); }
        else { unlink($file->getPathname()); }
    }
    rmdir($root);
}
echo json_encode(['schema' => 'peano-php-delivery-tests-v1', 'php' => PHP_VERSION,
    'passed' => count($passed), 'failed' => $failed, 'cases' => $passed,
    'peak_memory_bytes' => memory_get_peak_usage(true)], JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT), "\n";
exit(count($failed) === 0 ? 0 : 1);

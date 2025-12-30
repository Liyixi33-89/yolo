module.exports = {
  apps: [
    {
      name: 'yolo-backend',
      script: 'api_server.py',
      interpreter: './venv/bin/python3.9',
      cwd: '/var/www/yolo',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'production',
        PORT: 8000
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};

var glob = require('glob')
var path = require('path')

var config = require('./gulp/config.js')

var jsEntryPoints = glob.sync(path.join(config.sourcePath, 'javascripts/*.js'))

jsEntryPoints = jsEntryPoints.reduce((accumulator, value) => {
  accumulator[path.basename(value, '.js')] = path.resolve(value)
  return accumulator
}, {})

var node_paths = ['node_modules']
if (process.env.NODE_PATH) {
  node_paths.unshift(process.env.NODE_PATH)
}

module.exports = {
  mode: 'production',
  bail: true,
  devtool: 'source-map',
  entry: jsEntryPoints,
  output: {
    path: path.resolve(path.join(config.destinationPath, 'javascripts')),
    filename: '[name].js'
  },
  resolve: {
    modules: node_paths
  },
  resolveLoader: {
    modules: node_paths
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['babel-preset-env']
          }
        }
      }
    ]
  },
  watchOptions: {
    poll: true // inotify doesn't work inside VMs
  },
  stats: {
    assets: true,
    colors: true,
    entrypoints: false,
    hash: false,
    modules: false,
    version: false
  }
}

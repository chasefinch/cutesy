# Homebrew formula for Cutesy
# To install locally: brew install --build-from-source ./homebrew/cutesy.rb
# To add to homebrew-core: Submit PR to https://github.com/Homebrew/homebrew-core

class Cutesy < Formula
  include Language::Python::Virtualenv

  desc "A linter & formatter for consistent HTML code, or else."
  homepage "https://github.com/chasefinch/cutesy"
  url "https://github.com/chasefinch/cutesy/archive/refs/tags/v1.0b18.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"  # Get via: shasum -a 256 cutesy-VERSION.tar.gz
  license "Apache-2.0"
  # NOTE: Version is defined in cutesy/__init__.py - update URL and SHA256 manually here

  depends_on "python@3.12"
  depends_on "rust" => :build  # Only needed for building from source

  # Python dependencies
  resource "data-enum" do
    url "https://files.pythonhosted.org/packages/source/d/data-enum/data_enum-2.0.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.8.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  def install
    # Install Python dependencies into virtualenv
    virtualenv_install_with_resources

    # Generate shell completions (optional)
    generate_completions_from_executable(bin/"cutesy", shells: [:bash, :zsh, :fish])
  end

  test do
    # Test that the CLI works
    (testpath/"test.html").write <<~HTML
      <!doctype html>
      <html>
        <head>
          <title>Test</title>
        </head>
        <body>
          <h1>Hello, World!</h1>
        </body>
      </html>
    HTML

    system bin/"cutesy", "--check", testpath/"test.html"

    # Test that Rust extension loaded
    system Formula["python@3.12"].opt_bin/"python3", "-c",
      "from cutesy import cutesy_core; print(cutesy_core.hello_from_rust())"
  end
end

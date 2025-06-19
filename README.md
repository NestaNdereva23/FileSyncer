# File Syncer

A desktop application for synchronizing files between your local machine and Google Drive with a simple, user-friendly interface.

![File Syncer Screenshot](https://github.com/NestaNdereva23/FileSyncer/blob/main/filesyncer.png)

## Features

- 🔐 **Secure Google Drive Authentication** - OAuth2 integration with Google Drive API
- 📁 **File Management** - View, upload, and manage your Google Drive files
- 🔄 **Real-time Synchronization** - Keep your local files in sync with Google Drive
- 📊 **File Information** - View file sizes, types, and modification dates(in-progress)
- 🖥️ **Platform** - Currently tested on (Linux Mint 22.1 Cinnamon, Linux kernel -6.8.0-60-generic)
- 💾 **Local Database** - Tracks sync status and file metadata locally

## File Structure

```
filesyncer/
├── main.py              # Main application file
├── database.py          # Database operations
├── drive_manager.py     # Google Drive API integration
├── authenticate.py      # Authentication handling
├── credentials.json     # Google API credentials (user-provided)
├── icons/
│   └── filesyncer.svg   # Application icon
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## System Requirements

- **Operating System:** Linux (Ubuntu 24.04+)
- **Python:** 3.7+ (bundled in packaged version)
- **Disk Space:** ~50MB for installation

## Dependencies

### Python Packages
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`
- `PyQt5` 

### System Dependencies
- `PyQt5` (for GUI)
- `libssl3` (for secure connections)

## Configuration

The application stores its data in:
- **Database:** `~/.filesyncer/filesyncer.db`
- **Credentials:** Bundled with application or in app directory
- **Cache:** `~/.filesyncer/cache/` (temporary files)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/filesyncer/issues)
- **Email:** nestandereva@gmail.com
- **Documentation:** [Wiki](https://github.com/nestandereva23/filesyncer/wiki)

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Basic Google Drive integration
- File upload/download functionality
- GUI interface with PyQt5
- Debian package distribution(coming soon)

---

**Made with ❤️ for the open source community**
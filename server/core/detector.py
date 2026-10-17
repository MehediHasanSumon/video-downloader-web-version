"""Platform identification and profile resolution."""

from core.models import Platform

class PlatformDetector:
    """Detects and provides rich metadata for social media and video sharing platforms."""

    @staticmethod
    def detect(url: str) -> Platform:
        url_lower = url.lower()
        if any(d in url_lower for d in ["facebook.com", "fb.watch", "fb.com", "fb.me"]):
            return Platform(
                key="facebook",
                name="Facebook",
                badge="[bold #121316 on #60a4fa]  Facebook  [/]",
                color="bright_blue",
                icon="🔵",
                folder="Facebook",
                is_social=True,
            )
        elif any(d in url_lower for d in ["youtube.com", "youtu.be"]):
            return Platform(
                key="youtube",
                name="YouTube",
                badge="[bold #121316 on #f87070]  YouTube  [/]",
                color="bright_red",
                icon="🔴",
                folder="YouTube",
                is_social=False,
            )
        elif any(d in url_lower for d in ["instagram.com", "instagr.am"]):
            return Platform(
                key="instagram",
                name="Instagram",
                badge="[bold #121316 on #e778f9]  Instagram  [/]",
                color="bright_magenta",
                icon="🟣",
                folder="Instagram",
                is_social=True,
            )
        elif "tiktok.com" in url_lower:
            return Platform(
                key="tiktok",
                name="TikTok",
                badge="[bold #121316 on #27d2ed]  TikTok  [/]",
                color="bright_white",
                icon="⬛",
                folder="TikTok",
                is_social=True,
            )
        elif any(d in url_lower for d in ["twitter.com", "x.com"]):
            return Platform(
                key="twitter",
                name="Twitter",
                badge="[bold #121316 on #f3f4f6]  Twitter  [/]",
                color="bright_cyan",
                icon="🐦",
                folder="Twitter",
                is_social=True,
            )
        else:
            return Platform(
                key="generic",
                name="Web Media",
                badge="[bold #121316 on #4bdd7f]  Web Media  [/]",
                color="bright_green",
                icon="🌐",
                folder="WebMedia",
                is_social=False,
            )

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    curl \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Set up SSH
RUN mkdir /var/run/sshd
RUN echo 'PermitRootLogin no' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config

# Create CTF user
RUN useradd -m -s /bin/bash ctf
RUN echo "ctf:ctf123" | chpasswd

# Create flag
RUN mkdir -p /var/ctf
RUN echo "flag{unit221b_ctf_win}" > /var/ctf/flag.txt
RUN chmod 400 /var/ctf/flag.txt
RUN chown root:root /var/ctf/flag.txt

# Set permissions for CTF user
RUN chmod 711 /var/ctf

# Expose ports
EXPOSE 22 80

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"] 
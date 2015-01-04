# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
 config.vm.box = "hashicorp/precise64"
 
 dirname = File.basename(Dir.getwd)
 config.vm.hostname = dirname

 config.vm.network "forwarded_port", guest: 5000, host: 5005
 config.vm.network "forwarded_port", guest: 8080, host: 8085

$script = <<SCRIPT
echo "Provisioning Flask, RethinkDB, Python imaging libraries"
sudo apt-get update
sudo apt-get -y install python avahi-daemon python-pip git curl upstart python-dev build-essential libjpeg-dev libfreetype6-dev zlib1g-dev libpng12-dev

sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib
sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib
sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib

source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get -y install rethinkdb

sudo pip install PIL --upgrade
sudo pip install -r /vagrant/requirements.txt

sudo initctl emit vagrant-ready
SCRIPT

config.vm.provision "shell", inline: $script

end